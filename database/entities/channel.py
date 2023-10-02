from ..migrations import msqls


def create(id, name, user_id, loaded):
    cursor = msqls.db_execute_command(
        "INSERT INTO channels VALUES (?, ?, ?, ?)",
        (id, name, user_id, loaded)
    )
    return cursor


def create_recursive(list: list):
    if not list:
        return print("✅ Ended")
    item = list.pop()
    if item is None:
        return

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

    query = f"SELECT * FROM channels WHERE {where_clause};"

    cursor = msqls.db_execute_command(query, params)
    data = cursor.fetchone()
    # cursor.close()

    return data
