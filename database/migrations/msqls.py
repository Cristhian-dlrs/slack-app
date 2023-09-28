
import connection

con = connection.db_connection()

def init_db():
    users_table = """
        CREATE TABLE "dbo.users" (id text, team_id text, name text, real_name text);
        """
    db_execute_command(users_table)

def db_execute_command(sql_command):
    cursor = con.cursor()
    cursor.execute(sql_command)
    con.commit()
    cursor.close()
    con.close()
    




