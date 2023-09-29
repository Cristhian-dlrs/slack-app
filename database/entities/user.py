from migrations import msqls

def create(user_id, team_id, name, real_name):
    # query = "INSERT INTO users VALUES ('Starlin', 'hi', 'how yall doing', 'real name');"
    query = F"INSERT INTO users VALUES ('{user_id}', '{team_id}', '{name}', '{real_name}');"
    msqls.db_execute_command(query)
    
def create_recursive(list: list):
    item = list.pop()
    

