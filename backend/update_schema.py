import sqlite3
from database import DB_PATH

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List of schema updates (safe to run even if repeated)
updates = [
    ("category", "TEXT"),
    ("price", "INTEGER"),
    ("size_xxxl", "INTEGER"),
    ("last_updated", "TEXT")
]

print("Starting database schema update...")

for column_name, column_type in updates:
    try:
        cursor.execute(f"ALTER TABLE shirts ADD COLUMN {column_name} {column_type}")
        print(f"✅ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if f"duplicate column name: {column_name}" in str(e):
            print(f"⚠️ Column already exists: {column_name} (skipping)")
        else:
            print(f"❌ Error adding {column_name}: {e}")

# Commit changes
conn.commit()

# Optional: verify schema
cursor.execute("PRAGMA table_info(shirts)")
columns = cursor.fetchall()

print("\nCurrent columns:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

# Close connection
conn.close()

print("\n✅ Schema update complete.")
