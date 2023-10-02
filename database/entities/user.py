from ..migrations import msqls


def create(user_id, team_id, name, real_name):
    # query = "INSERT INTO users VALUES ('Starlin', 'hi', 'how yall doing', 'real name');"
    # query = F'INSERT INTO users VALUES ("{user_id}", "{team_id}", "{name}", "{real_name}");'

    msqls.db_execute_command(
        "INSERT INTO users VALUES (?, ?, ?, ?)",
        (user_id, team_id, name, real_name)
    )


def create_recursive(list: list):
    if not list:
        return print("✅ Ended")
    item = list.pop()
    if item is None:
        return
    existUser = find(user_id=item["id"])
    if existUser:
        return print("👤ℹ️ User Exist", item["name"]), create_recursive(list)
    print("👤 Saving", item["name"])
    create(item["id"], item["team_id"], item["name"],
           item["profile"]["real_name"])
    create_recursive(list)


def find(**kwargs):
    conditions = []
    params = []

    for key, value in kwargs.items():
        conditions.append(f"{key} = ?")
        params.append(value)

    where_clause = " AND ".join(conditions)

    query = f"SELECT * FROM users WHERE {where_clause};"

    cursor = msqls.db_execute_command(query, params)
    user = cursor.fetchone()
    # cursor.close()

    return user
