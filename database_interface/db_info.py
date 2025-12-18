import sqlite3

DATABASE_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def initialize_sso_table():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS sso_configurations (
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            callback_url TEXT NOT NULL,
            scope TEXT NOT NULL
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS Character_info (
            character_id TEXT NOT NULL,
            character_name TEXT NOT NULL,
            Character_owner_hash TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL   
        )
        ''')
        conn.commit()
        
initialize_sso_table()