
from ..connection import db_connection
from ..entities import user

con = db_connection()


def init_db():
    initMigration = """
            IF OBJECT_ID(N'dbo.users', N'U') IS NULL CREATE TABLE users (
                id int primary key(id) identity(1,1), "user_id" nvarchar(30) unique NOT NULL, team_id text, name text, real_name text
            );

            IF OBJECT_ID(N'dbo.channels', N'U') IS NULL CREATE table channels(
                id int primary key(id) identity(1,1), name text, user_id  nvarchar(30), loaded INT,
                constraint fk_channelUser FOREIGN KEY (user_id) references users (user_id)
            );

            IF OBJECT_ID(N'dbo.messages', N'U') IS NULL CREATE table messages(
                id int primary key(id) identity(1,1),
                type TEXT,
                text TEXT,
                ts int,
                user_id nvarchar(30) NOT NULL,
                channel int,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (channel) REFERENCES channels (id)
            );
        """

    db_execute_command(initMigration)


def db_execute_command(sql_command):
    cursor = con.cursor()
    cursor.execute(sql_command)
    con.commit()
    cursor.close()
    con.close()
