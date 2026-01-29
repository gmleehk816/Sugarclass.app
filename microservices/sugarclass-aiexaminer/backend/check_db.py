import sqlite3
import os

db_path = '/app/database/examiner.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
print(f"Tables: {tables}")

for table in tables:
    cursor.execute(f"SELECT count(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

    # Get schema
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
    schema = cursor.fetchone()[0]
    print(f"Schema for {table}:\n{schema}\n")
