import sqlite3
import datetime
import uuid

DB_PATH = "rice_bug.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS identifications (
            id TEXT PRIMARY KEY,
            image_path TEXT, -- legacy, will store original_path for old records
            original_path TEXT,
            thumbnail_path TEXT,
            pred1_class TEXT,
            pred1_prob REAL,
            pred2_class TEXT,
            pred2_prob REAL,
            pred3_class TEXT,
            pred3_prob REAL,
            is_correct INTEGER DEFAULT -1, -- -1 for unset, 1 for correct, 0 for incorrect
            corrected_class TEXT,
            timestamp TEXT
        )
    ''')
    
    # Simple migration: check if columns exist
    cursor.execute("PRAGMA table_info(identifications)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'original_path' not in columns:
        cursor.execute("ALTER TABLE identifications ADD COLUMN original_path TEXT")
    if 'thumbnail_path' not in columns:
        cursor.execute("ALTER TABLE identifications ADD COLUMN thumbnail_path TEXT")
        
    conn.commit()
    conn.close()

def log_identification(original_path, thumbnail_path, predictions):
    id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO identifications (
            id, image_path, original_path, thumbnail_path, 
            pred1_class, pred1_prob, pred2_class, pred2_prob, pred3_class, pred3_prob, 
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        id, original_path, original_path, thumbnail_path,
        predictions[0]['class'], predictions[0]['probability'],
        predictions[1]['class'], predictions[1]['probability'],
        predictions[2]['class'], predictions[2]['probability'],
        timestamp
    ))
    conn.commit()
    conn.close()
    return id

def update_feedback(id, is_correct, corrected_class=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE identifications
        SET is_correct = ?, corrected_class = ?
        WHERE id = ?
    ''', (1 if is_correct else 0, corrected_class, id))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM identifications ORDER BY timestamp DESC')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
