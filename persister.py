import sqlite3

conn = sqlite3.connect('slack.db')
cursor = conn.cursor()


def init_db():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT         PRIMARY KEY,
            team_id         TEXT,
            name            TEXT,
            real_name       TEXT,
        )
        """

    )
