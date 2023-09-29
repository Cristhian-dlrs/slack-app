import os
import pyodbc
import sqlite3
from dotenv import load_dotenv

env_file = os.path.join(os.path.dirname(__file__), "../.env")
if os.path.isfile(env_file):
    load_dotenv(env_file)

DB_NAME = 'slack.db'

def db_connection():
    db_type = os.getenv('DB_TYPE'); 
    con = None
    print("💾 Connection :", os.getenv("DB_DRIVER"))
    connectionString = f"""
            DRIVER={{{os.getenv("DB_DRIVER")}}};
            SERVER={{{os.getenv("DB_SERVER")}}};
            DATABASE={{{os.getenv("DB_DATABASE")}}};
            TRUSTED_CONNECTION={{{os.getenv("DB_TRUSTED_CONNECTION")}}};
        """
    if db_type == "MSQLS":  
        con = pyodbc.connect(connectionString)
        con.autocommit = True
    else: 
        con = sqlite3.connect(DB_NAME)
    return con
