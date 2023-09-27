#!/usr/bin/env python3
import os
import sys
import requests
import json
import time
from datetime import datetime
import argparse
from dotenv import load_dotenv
from time import sleep
import sqlite3


DB_NAME = 'slack.db'
# when rate-limited, add this to the wait time
ADDITIONAL_SLEEP_TIME = 5
RETRY_LIMIT = 10

env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.isfile(env_file):
    load_dotenv(env_file)


# =================================================================================================
# UTILS
# =================================================================================================
def progressbar(it, prefix="", size=60, out=sys.stdout):
    count = len(it)
    start = time.time()

    def show(j):
        x = int(size*j/count)
        remaining = ((time.time() - start) / j) * (count - j)

        mins, sec = divmod(remaining, 60)
        time_str = f"{int(mins):02}:{sec:05.2f}"

        print(f"[{u'#'*x}{('.'*(size-x))}] {j}/{count} {prefix} Est wait {time_str}",
              end='\r', file=out, flush=True)

    for i, item in enumerate(it):
        yield item
        show(i+1)
    print("\n", flush=True, file=out)


def to_unixts(date_str):
    date = datetime.strptime(date_str, "%d/%m/%Y")
    ts = int(date.timestamp())
    return ts


def from_unixts(ts):
    date = datetime.fromtimestamp(ts)
    formatted_date = date.strftime('%d/%m/%Y %H:%M:%S')
    return formatted_date

# =================================================================================================
# HTTP
# =================================================================================================


def post_response(response_url, text):
    requests.post(response_url, json={"text": text})


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
            sleep(sleep_time)
        if attempt >= RETRY_LIMIT:
            print(
                "Downloading process stopped due retry attempt limit, please continue later.")
            try:
                sys.exit(130)
            except SystemExit:
                os._exit(130)
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


def channel_list(team_id=None, response_url=None):
    params = {
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


def channel_history(channel_id, response_url=None, oldest=None, latest=None):
    params = {
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
    for user in progressbar(data, prefix='Loading users:'):
        users.append((user["id"], user["team_id"],
                      user["name"], user["profile"]["real_name"]))
        time.sleep(0.01)

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
    for channel in progressbar(data, prefix='Loading channels:'):
        channels.append((channel["id"],
                         channel["name"] if "name" in channel
                         else user_name(channel["user"]),
                         channel["user"] if "user" in channel else "IS GROUP",
                         0))
        time.sleep(0.01)

    insert_query = "INSERT INTO channels Values(?, ?, ?, ?)"
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
        channels.append({'id': channel[0], 'chanel_name': channel[1],
                        'user': channel[2], 'is_loaded': channel[3]})
    return channels


def export_channel_history(channel_name):
    channel = get_channels(channel_name)[0]
    if channel['is_loaded'] == 1:
        print("Channel messages already loaded")
        return

    data = channel_history(channel['id'])
    save_messages(channel['id'], data)
    update_query = f"UPDATE channels SET loaded = 1 WHERE id = '{channel['id']}'"
    db_execute_command(update_query)


def save_messages(channel_id, data):
    messages = []
    for message in progressbar(data, prefix='Loading messages:'):
        messages.append((message["client_msg_id"] if "client_msg_id" in message else "INFO",
                         message["type"], message["text"], message["ts"],
                         message["user"] if "user" in message else "UNKNOWN", channel_id))
        time.sleep(0.0001)

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
        WHERE channels.name = '{channel}' AND messages.fr > {fr}
        ORDER BY messages.ts ASC
        """
    elif channel is not None and fr is None and to is not None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        WHERE channels.name = '{channel}' AND messages.fr < {to}
        ORDER BY messages.ts ASC
        """
    elif channel is not None and fr is not None and to is not None:
        query = f"""
        SELECT messages.text, users.real_name, channels.name, messages.ts
        from messages inner join users on messages.user = users.id
        inner join channels on messages.channel = channels.id
        WHERE channels.name = '{channel}' AND messages.fr < {to} AND messages.fr < {to}
        ORDER BY messages.ts ASC
        """

    res = db_execute_query(query)
    messages = []
    for message in res:
        messages.append(
            {'message': message[0], 'user': message[1], 'channel': message[2], 'date': from_unixts(message[3])})
    return messages


def search_messages(search, channel=None):
    query = ''
    if channel is None:
        query = f"""
            SELECT messages.text, users.real_name, channels.name, messages.ts
            from messages inner join users on messages.user = users.id
            inner join channels on messages.channel = channels.id
            WHERE messages.text LIKE '%{search}%'
            ORDER BY messages.ts ASC
            """
    else:
        query = f"""
            SELECT messages.text, users.real_name, channels.name, messages.ts
            from messages inner join users on messages.user = users.id
            inner join channels on messages.channel = channels.id
            WHERE channels.name = '{channel} AND messages.text LIKE '%{search}%'
            ORDER BY messages.ts ASC
            """

    res = db_execute_query(query)
    messages = []
    for message in res:
        messages.append(
            {'message': message[0], 'user': message[1], 'channel': message[2], 'date': from_unixts(message[3])})
    return messages


def init_db():
    print("Initializing database...")
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
                loaded INTEGER,
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


def export_slack_data():
    init_db()

    print("Exporting slack data...")
    users = user_list()
    save_users(users)

    channels = channel_list()
    save_channels(channels)
    print("Application initialization completed!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init",
        action="store_true",
        help="Exports all users and channels from slack",
    )

    parser.add_argument(
        "--dch",
        action="store_true",
        help="Exports the history of messages for a specific channel",
    )

    parser.add_argument(
        "--msg",
        action="store_true",
        help="Get all messages",
    )

    parser.add_argument(
        "-s",
        help="With --msg, search for messages that contains the specified search term"
    )

    parser.add_argument(
        "--ch",
        help="With --msg, restrict messages to given channel name"
    )

    parser.add_argument(
        "--fr",
        help="With --msg, date for earliest message (dd/mm/yyyy)",
        type=str,
    )
    parser.add_argument(
        "--to",
        help="With --msg, date for latest message (dd/mm/yyyy)",
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
        help="Name of the channel to load history if called with --dch\
              Name of the channel to retrieve if called with --lc\
              Name of the user to retrieve if called with --lu"
    )

    args = parser.parse_args()

    if args.init:
        try:
            export_slack_data()
        except Exception as e:
            print(f"The application is already initialized")

    if args.dch:
        export_channel_history(args.n)

    if args.lc:
        res = get_channels(args.n) if args.n else get_channels()
        print(json.dumps(res, indent=4))

    if args.lu:
        res = get_users(args.n) if args.n else get_users()
        print(json.dumps(res, indent=4))

    if args.msg:
        if args.s:
            res = search_messages(args.s)
            print(json.dumps(res, indent=4))

        elif args.s and args.ch:
            res = search_messages(args.s, args.ch)
            print(json.dumps(res, indent=4))

        elif args.ch and args.fr and args.to:
            res = get_messages(args.ch, to_unixts(args.fr), to_unixts(args.to))
            print(json.dumps(res, indent=4))

        elif args.ch:
            res = get_messages(args.ch)
            print(json.dumps(res, indent=4))

        elif args.to and args.fr:
            res = get_messages(None, to_unixts(args.fr), to_unixts(args.to))
            print(json.dumps(res, indent=4))

        elif args.to:
            res = get_messages(None, None, to_unixts(args.to))
            print(json.dumps(res, indent=4))

        elif args.fr:
            res = get_messages(None, to_unixts(args.fr), None)
            print(json.dumps(res, indent=4))

        else:
            res = get_messages()
            print(json.dumps(res, indent=4))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nExited!')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
