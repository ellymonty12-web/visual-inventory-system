import sqlite3
from database import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Updating NULL categories to default...")

try:
    cursor.execute("""
        UPDATE shirts
        SET category = 'adult_10'
        WHERE category IS NULL OR category = ''
    """)
    conn.commit()

    print(f"✅ Rows updated: {cursor.rowcount}")

except Exception as e:
    print(f"❌ Error: {e}")

# Verify results
print("\nCurrent categories:")
cursor.execute("""
    SELECT DISTINCT category FROM shirts
""")
rows = cursor.fetchall()

for row in rows:
    print(f"- {row[0]}")

conn.close()

print("\n✅ Category fix complete.")