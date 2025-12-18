import sqlite3
from .db_info import get_db_connection

def load_sso_config():
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute('SELECT client_id, client_secret, callback_url FROM sso_configurations LIMIT 1')
            config = c.fetchone()
            if config:
                return config
            else:
                return None
        except sqlite3.OperationalError as e:
            print(f"Error loading SSO configurations: {e}")
            return None

def save_sso_config(client_id, client_secret, callback_url):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM sso_configurations')
        c.execute('INSERT INTO sso_configurations (client_id, client_secret, callback_url) VALUES (?, ?, ?)',
                  (client_id, client_secret, callback_url))
        conn.commit()