import sqlite3
from database import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

updates = [
    ("size_6m", "INTEGER"),
    ("size_12m", "INTEGER"),
    ("size_24m", "INTEGER"),
]

print("Adding child size columns...")

for column_name, column_type in updates:
    try:
        cursor.execute(f"ALTER TABLE shirts ADD COLUMN {column_name} {column_type}")
        print(f"✅ Added: {column_name}")
    except sqlite3.OperationalError as e:
        if f"duplicate column name: {column_name}" in str(e):
            print(f"⚠️ Already exists: {column_name}")
        else:
            print(f"❌ Error: {e}")

conn.commit()

# Verify
cursor.execute("PRAGMA table_info(shirts)")
columns = cursor.fetchall()

print("\nCurrent columns:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()

print("\n✅ Child size update complete.")
