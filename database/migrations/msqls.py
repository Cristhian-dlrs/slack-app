
from ..connection import db_connection
# from ..entities import user

con = db_connection()


def init_db():
    print("💾 Validating Migration...")
    initMigration = """
               IF OBJECT_ID(N'dbo.users', N'U') IS NULL 
            CREATE TABLE users (
                id int PRIMARY KEY IDENTITY(1,1),
                user_id nvarchar(300) UNIQUE NOT NULL,
                team_id text,
                name nvarchar(300),
                real_name nvarchar(300)
            );

            IF OBJECT_ID(N'dbo.channels', N'U') IS NULL 
            CREATE TABLE channels (
                id nvarchar(300) PRIMARY KEY,
                name nvarchar(300),
                user_id nvarchar(300),  -- Match the length and data type
                loaded INT,
                CONSTRAINT fk_channelUser FOREIGN KEY (user_id) REFERENCES users (user_id)
            );

            IF OBJECT_ID(N'dbo.messages', N'U') IS NULL 
            CREATE TABLE messages (
                id int PRIMARY KEY IDENTITY(1,1),
                type nvarchar(300),
                text nvarchar(300),
                ts nvarchar(300),
                user_id nvarchar(300) NOT NULL,
                channel_id nvarchar(300),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (channel_id) REFERENCES channels (id)
            );
        );
        """

    db_execute_command(initMigration)


def db_execute_command(sql_command, params=None):
    try:
        cursor = con.cursor()
        if params:
            cursor.execute(sql_command, params)
        else:
            cursor.execute(sql_command)
        con.commit()
        # cursor.close()
        return cursor
    except Exception as e:
        print(f"Error executing SQL command: {str(e)}")


def db_execute_many(sql_query, data):
    cursor = con.cursor()
    cursor.executemany(sql_query, data)
    result = cursor.fetchall()
    con.commit()
    cursor.close()
    con.close()
