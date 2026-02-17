import sqlite3
import os
from pathlib import Path

DB_PATH = Path("e:/PROGRAMMING/Projects/Sugarclass.app/microservices/sugarclass-aimaterials/app/database/rag_content.db")
SCHEMA_PATH = Path("e:/PROGRAMMING/Projects/Sugarclass.app/microservices/sugarclass-aimaterials/app/schema_v8.sql")

def init_db():
    print(f"Initializing DB: {DB_PATH}")
    print(f"Using Schema: {SCHEMA_PATH}")
    
    if not SCHEMA_PATH.exists():
        print("Schema file not found!")
        return

    # Ensure directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute script (multiple statements)
        conn.executescript(schema_sql)
        conn.commit()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
