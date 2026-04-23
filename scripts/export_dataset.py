import sqlite3
import os
import shutil
import datetime

DB_PATH = "server_data/rice_bug.db"
EXPORT_DIR = "dataset_extend"

def export_dataset():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    print(f"Exporting dataset to {EXPORT_DIR}...")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query all records
        cursor.execute("SELECT * FROM identifications")
        rows = cursor.fetchall()

        if not rows:
            print("No records found in database.")
            conn.close()
            return

        # Counter for reporting
        count = 0
        skipped = 0

        for row in rows:
            # Determine class name
            # Priority: Corrected class (if is_correct is false), else predicted class
            class_name = row['pred1_class']
            if row['is_correct'] == 1: continue
            if row['is_correct'] == 0 and row['corrected_class']:
                class_name = row['corrected_class']
            
            if not class_name:
                class_name = "unknown"

            # Create class directory
            class_dir = os.path.join(EXPORT_DIR, class_name)
            if not os.path.exists(class_dir):
                os.makedirs(class_dir)

            # Source image path
            src_path = row['original_path']
            
            if not src_path or not os.path.exists(src_path):
                # Try to find it if path is relative or different
                # Sometimes paths are stored relative to different roots
                skipped += 1
                continue

            # New filename: use timestamp and ID to be unique and descriptive
            # Format: YYYYMMDD_HHMMSS_ID.ext
            ext = os.path.splitext(src_path)[1]
            # Replace spaces and colons in timestamp for filename safety
            ts_safe = row['timestamp'].replace(' ', '_').replace(':', '')
            new_filename = f"{ts_safe}_{row['id']}{ext}"
            
            dst_path = os.path.join(class_dir, new_filename)

            # Copy image
            shutil.copy2(src_path, dst_path)
            count += 1

        conn.close()
        print(f"Export completed. Successfully copied {count} images.")
        if skipped > 0:
            print(f"Skipped {skipped} records due to missing image files.")

    except Exception as e:
        print(f"An error occurred during export: {e}")

if __name__ == "__main__":
    export_dataset()
