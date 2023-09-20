#!/usr/bin/env python3
import os
import sys
import requests
import json
from timeit import default_timer
from datetime import datetime
import argparse
from dotenv import load_dotenv
from pathvalidate import sanitize_filename
from time import sleep
import sqlite3
import json


DB_NAME = 'slack.db'
# when rate-limited, add this to the wait time
ADDITIONAL_SLEEP_TIME = 10

env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.isfile(env_file):
    load_dotenv(env_file)


# =================================================================================================
# HTTP
# =================================================================================================
def post_response(response_url, text):
    requests.post(response_url, json={"text": text})


# use this to say anything
# will print to stdout if no response_url is given
# or post_response to given url if provided
def handle_print(text, response_url=None):
    if response_url is None:
        print(text)
    else:
        post_response(response_url, text)


# slack api (OAuth 2.0) now requires auth tokens in HTTP Authorization header
# instead of passing it as a query parameter
try:
    HEADERS = {"Authorization": "Bearer %s" % os.environ["SLACK_USER_TOKEN"]}
except KeyError:
    handle_print(
        "Missing SLACK_USER_TOKEN in environment variables")
    sys.exit(1)


def _get_data(url, params):
    return requests.get(url, headers=HEADERS, params=params)


def get_data(url, params):
    """Naively deals with rate-limiting"""

    # success means "not rate-limited", it can still end up with error
    success = False
    attempt = 0

    while not success:
        r = _get_data(url, params)
        attempt += 1

        if r.status_code != 429:
            success = True
        else:
            retry_after = int(r.headers["Retry-After"])  # seconds to wait
            sleep_time = retry_after + ADDITIONAL_SLEEP_TIME
            print(
                f"Rate-limited. Retrying after {sleep_time} seconds ({attempt}x).")
            sleep(sleep_time)
    return r

# =================================================================================================
# Pagination handling
# =================================================================================================


def get_at_cursor(url, params, cursor=None, response_url=None):
    if cursor is not None:
        params["cursor"] = cursor

    r = get_data(url, params)

    if r.status_code != 200:
        handle_print("ERROR: %s %s" % (r.status_code, r.reason), response_url)
        sys.exit(1)

    d = r.json()

    try:
        if d["ok"] is False:
            handle_print("I encountered an error: %s" % d, response_url)
            sys.exit(1)

        next_cursor = None
        if "response_metadata" in d and "next_cursor" in d["response_metadata"]:
            next_cursor = d["response_metadata"]["next_cursor"]
            if str(next_cursor).strip() == "":
                next_cursor = None

        return next_cursor, d

    except KeyError as e:
        handle_print("Something went wrong: %s." % e, response_url)
        return None, []


def paginated_get(url, params, combine_key=None, response_url=None):
    next_cursor = None
    result = []
    while True:
        next_cursor, data = get_at_cursor(
            url, params, cursor=next_cursor, response_url=response_url
        )

        try:
            result.extend(data) if combine_key is None else result.extend(
                data[combine_key]
            )
        except KeyError as e:
            handle_print("Something went wrong: %s." % e, response_url)
            sys.exit(1)

        if next_cursor is None:
            break

    return result

# =================================================================================================
# GET requests
# =================================================================================================


def channel_list(team_id=None, response_url=None):
    params = {
        # "token": os.environ["SLACK_USER_TOKEN"],
        "team_id": team_id,
        "types": "public_channel,private_channel,mpim,im",
        "limit": 200,
    }

    return paginated_get(
        "https://slack.com/api/conversations.list",
        params,
        combine_key="channels",
        response_url=response_url,
    )


def get_file_list():
    current_page = 1
    total_pages = 1
    while current_page <= total_pages:
        response = get_data("https://slack.com/api/files.list",
                            params={"page": current_page})
        json_data = response.json()
        total_pages = json_data["paging"]["pages"]
        for file in json_data["files"]:
            yield file
        current_page += 1


def channel_history(channel_id, response_url=None, oldest=None, latest=None):
    params = {
        # "token": os.environ["SLACK_USER_TOKEN"],
        "channel": channel_id,
        "limit": 200,
    }

    if oldest is not None:
        params["oldest"] = oldest
    if latest is not None:
        params["latest"] = latest

    return paginated_get(
        "https://slack.com/api/conversations.history",
        params,
        combine_key="messages",
        response_url=response_url,
    )


def user_list(team_id=None, response_url=None):
    params = {
        # "token": os.environ["SLACK_USER_TOKEN"],
        "limit": 200,
        "team_id": team_id,
    }

    return paginated_get(
        "https://slack.com/api/users.list",
        params,
        combine_key="members",
        response_url=response_url,
    )


def channel_replies(timestamps, channel_id, response_url=None):
    replies = []
    for timestamp in timestamps:
        params = {
            # "token": os.environ["SLACK_USER_TOKEN"],
            "channel": channel_id,
            "ts": timestamp,
            "limit": 200,
        }
        replies.append(
            paginated_get(
                "https://slack.com/api/conversations.replies",
                params,
                combine_key="messages",
                response_url=response_url,
            )
        )

    return replies


# =================================================================================================
# SQL
# =================================================================================================
def db_execute_command(sql_command):
    con = sqlite3.connect(DB_NAME)
    cursor = con.cursor()
    cursor.execute(sql_command)
    con.commit()
    cursor.close()
    con.close()


def db_execute_query(sql_query):
    con = sqlite3.connect(DB_NAME)
    cursor = con.cursor()
    cursor.execute(sql_query)
    result = cursor.fetchall()
    cursor.close()
    con.close()
    return result


def db_execute_many(sql_query, data):
    con = sqlite3.connect(DB_NAME)
    cursor = con.cursor()
    cursor.executemany(sql_query, data)
    result = cursor.fetchall()
    con.commit()
    cursor.close()
    con.close()


def save_users(data):
    insert_query = "INSERT INTO users Values(?, ?, ?, ?)"
    users = []
    for user in data:
        users.append((user["id"], user["team_id"],
                      user["name"], user["profile"]["real_name"]))

    db_execute_many(insert_query, users)


def get_users(name=None):
    query = ""
    if name is None:
        query = "SELECT * FROM users"
    else:
        query = f"SELECT * FROM users where real_name = '{name}'"

    res = db_execute_query(query)
    users = []
    for user in res:
        users.append(
            {'id': user[0], 'team_id': user[1], 'name': user[2], 'real_name': user[3]})

    return users


def save_channels(data):
    users = get_users()

    def user_name(id):
        for user in users:
            if user["id"] == id:
                return user["real_name"]

    channels = []
    for channel in data:
        channels.append((channel["id"],
                         channel["name"] if "name" in channel
                         else user_name(channel["user"]),
                         channel["user"] if "user" in channel else "IS GROUP"))

    insert_query = "INSERT INTO channels Values(?, ?, ?)"
    db_execute_many(insert_query, channels)


def get_channels(name=None):
    query = ""
    if name is None:
        query = "SELECT * FROM channels"
    else:
        query = f"SELECT * FROM channels where name = '{name}'"

    res = db_execute_query(query)
    channels = []
    for channel in res:
        channels.append(
            {'id': channel[0], 'chanel_name': channel[1], 'user': channel[2]})
    return channels


def save_messages(channel_id, data):
    messages = []
    for message in data:
        messages.append((message["client_msg_id"] if "client_msg_id" in message else "INFO",
                         message["type"], message["text"], message["ts"],
                         message["user"] if "user" in message else "UNKNOWN", channel_id))

    insert_query = "INSERT INTO messages Values(?, ?, ?, ?, ?, ?)"
    db_execute_many(insert_query, messages)


def get_messages(channel=None, fr=None, to=None):
    query = ""
    if channel is None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        ORDER BY messages.ts ASC
        """

    elif channel is not None and fr is None and to is None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        WHERE channels.name = '{channel}'
        ORDER BY messages.ts ASC
        """
    elif channel is not None and fr is not None and to is None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        WHERE channels.name = '{channel} AND messages.fr > {fr}
        ORDER BY messages.ts ASC
        """
    elif channel is not None and fr is None and to is not None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        WHERE channels.name = '{channel} AND messages.fr < {to}
        ORDER BY messages.ts ASC
        """
    elif channel is not None and fr is not None and to is not None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        WHERE channels.name = '{channel} AND messages.fr < {to} AND messages.fr < {to}
        ORDER BY messages.ts ASC
        """

    res = db_execute_query(query)
    messages = []
    for channel in res:
        messages.append(
            {'message': channel[0], 'user': channel[1], 'channel': channel[2], 'ts': channel[3]})
    return messages


def init_app():
    print("Generating database...")
    users_table = """
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            team_id TEXT,
            name TEXT,
            real_name TEXT
        );"""

    channels_table = """
        CREATE TABLE IF NOT EXISTS channels(
            id TEXT PRIMARY KEY,
            name TEXT,
            user TEXT,
            FOREIGN KEY (user) REFERENCES users (id)
        );"""

    messages_table = """
        CREATE TABLE IF NOT EXISTS messages(
            id TEXT,
            type TEXT,
            text TEXT,
            ts INTEGER,
            user TEXT,
            channel TEXT,
            PRIMARY KEY (channel, ts),
            FOREIGN KEY (user) REFERENCES users (id),
            FOREIGN KEY (channel) REFERENCES channels (id)
        );"""

    db_execute_command(users_table)
    db_execute_command(channels_table)
    db_execute_command(messages_table)

    print("Loading slack users...")

    users = user_list()
    save_users(users)

    print("Loading slack channels...")
    channels = channel_list()
    save_channels(channels)

    print("Loading slack conversations, it may take a while...")
    count = 1
    for channel in channels:
        print(f"{count} conversation loaded of {len(channels)}")
        data = channel_history(channel["id"])
        save_messages(channel["id"], data)
        count += 1
    print("App initialization completed!")


if __name__ == "__main__":
    # data = channel_history("CU616909X")
    # print(json.dumps(data, indent=4))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initializes de database exports all your data from slack",
    )

    parser.add_argument(
        "--msg",
        action="store_true",
        help="Get all messages",
    )

    parser.add_argument(
        "--ch",
        help="With --msg, restrict messages to given channel name"
    )

    parser.add_argument(
        "--fr",
        help="With --msg, Unix timestamp for earliest message",
        type=str,
    )
    parser.add_argument(
        "--to",
        help="With --msg, Unix timestamp for latest message",
        type=str,
    )

    parser.add_argument(
        "--lc",
        action="store_true",
        help="List all channels",
    )

    parser.add_argument(
        "--lu",
        action="store_true",
        help="List all users",
    )

    parser.add_argument(
        "-n",
        help="Name of the channel to retrieve if called with --lc\
            name of the user to retrieve if called with --lu"
    )

    args = parser.parse_args()

    if args.init:
        init_app()

    if args.lc:
        res = get_channels(args.n) if args.n else get_channels()
        print(json.dumps(res, indent=4))

    if args.lu:
        res = get_users(args.n) if args.n else get_users()
        print(json.dumps(res, indent=4))

    if args.msg:
        res = get_messages(
            args.ch, args.fr, args.to) if args.ch else get_messages()
        print(json.dumps(res, indent=4))
