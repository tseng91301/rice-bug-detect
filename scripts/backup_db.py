import sqlite3
import datetime
import os

DB_PATH = "server_data/rice_bug.db"
BACKUP_DIR = "backups"

def backup_database():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Generate filename with date and time
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.sql")

    print(f"Backing up database to {backup_file}...")

    try:
        conn = sqlite3.connect(DB_PATH)
        with open(backup_file, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        print("Backup completed successfully.")
    except Exception as e:
        print(f"An error occurred during backup: {e}")

if __name__ == "__main__":
    backup_database()
