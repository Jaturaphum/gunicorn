import os
import sqlite3

def get_db_connection():
    project_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.environ.get("DATABASE_PATH", os.path.join(project_directory, "database.db"))
    database_directory = os.path.dirname(database_path)
    if database_directory:
        os.makedirs(database_directory, exist_ok=True)
    database_connection = sqlite3.connect(database_path, timeout=30)
    database_connection.row_factory = sqlite3.Row
    database_connection.execute("PRAGMA foreign_keys = ON")
    return database_connection

def get_db_cursor(database_connection, dictionary=False):
    cursor = database_connection.cursor()
    return cursor

def execute_query(database_cursor, query, parameters=()):
    res = database_cursor.execute(query, parameters)
    return res

def init_db():
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "CREATE TABLE IF NOT EXISTS links (id TEXT PRIMARY KEY)")
    execute_query(database_cursor, "CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY AUTOINCREMENT, link_id TEXT, username TEXT, ip_address TEXT, user_agent TEXT, latitude REAL, longitude REAL, accuracy_meters REAL, session_id TEXT, is_sharing INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(link_id) REFERENCES links(id))")
    execute_query(database_cursor, "PRAGMA table_info(visits)")
    existing_columns = {column["name"] for column in database_cursor.fetchall()}
    missing_columns = (("accuracy_meters", "REAL"), ("session_id", "TEXT"), ("is_sharing", "INTEGER NOT NULL DEFAULT 0"))
    for column_name, column_type in missing_columns:
        if column_name not in existing_columns:
            execute_query(database_cursor, f"ALTER TABLE visits ADD COLUMN {column_name} {column_type}")
    execute_query(database_cursor, "CREATE INDEX IF NOT EXISTS idx_visits_session_id ON visits (session_id)")
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    return True