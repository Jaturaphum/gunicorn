import sqlite3
import sys
import api

def migrate(source_path):
    source_connection = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    source_cursor = source_connection.cursor()
    source_cursor.execute("SELECT id FROM links")
    link_rows = source_cursor.fetchall()

    source_cursor.execute("PRAGMA table_info(visits)")
    visit_columns = {column[1] for column in source_cursor.fetchall()}
    accuracy_column = "accuracy_meters" if "accuracy_meters" in visit_columns else "NULL"
    source_cursor.execute(
        f"""
        SELECT id, link_id, username, ip_address, user_agent, latitude, longitude,
        {accuracy_column}, created_at
        FROM visits
        """
    )
    visit_rows = source_cursor.fetchall()
    source_connection.close()

    api.init_db()
    target_connection = api.get_db_connection()
    target_cursor = target_connection.cursor()
    target_cursor.executemany(
        "INSERT IGNORE INTO links (id) VALUES (%s)",
        link_rows,
    )
    migrated_links = target_cursor.rowcount
    target_cursor.executemany(
        """
        INSERT IGNORE INTO visits (
            id, link_id, username, ip_address, user_agent, latitude, longitude,
            accuracy_meters, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        visit_rows,
    )
    migrated_visits = target_cursor.rowcount
    target_connection.commit()
    target_cursor.close()
    target_connection.close()
    print(f"Migrated {migrated_links} links and {migrated_visits} visits.")
    print("The SQLite source file was opened read-only and was not changed.")


if __name__ == "__main__":
    source_path = sys.argv[1] if len(sys.argv) > 1 else "database.db"
    migrate(source_path)
