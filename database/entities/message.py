from database.entities.channel import create as create_channel, find as find_channel
from meneo import channel_history
from ..migrations import msqls


def create(type, text, ts, user_id, channel_id):
    msqls.db_execute_command(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
        (type, text, ts, user_id, channel_id)
    )


def create_recursive(list: list):
    # print(list)
    if not list:
        return print("✅ Messages Ended")
    item = list.pop()
    if item is None:
        return

    # print("Loading Messages")
    messages = channel_history(item["id"])
    # print("Loaded Messages")
    if not messages:
        print("Not Message in this channel", item["id"])
        create_recursive(list)
        return

    for message in messages:
        # print(item)
        existChannel = find_channel(name=item['id'])
        if existChannel:
            print("Channel exist")
            create_recursive(list)
            return

        channel_created = create_channel(
            item["id"], item["id"], message["user"], 1)

        print(channel_created)

        create(message["type"], message["text"],
               message["ts"], message["user"], item["id"])

    create_recursive(list)


def find(**kwargs):
    conditions = []
    params = []

    for key, value in kwargs.items():
        conditions.append(f"{key} = ?")
        params.append(value)

    where_clause = " AND ".join(conditions)

    query = f"SELECT * FROM messages WHERE {where_clause};"

    cursor = msqls.db_execute_command(query, params)
    user = cursor.fetchone()
    # cursor.close()

    return user
