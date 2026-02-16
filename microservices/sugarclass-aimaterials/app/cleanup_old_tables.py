#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up old pipeline tables from V8 database.
Removes: content_raw, content_processed, exercises, questions tables
"""
import sqlite3
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Get paths
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "database" / "rag_content.db"

def cleanup_old_tables():
    """Remove old pipeline tables."""
    print(f"Cleaning up old tables in: {DB_PATH}")

    if not DB_PATH.exists():
        print("[ERROR] Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Old tables to drop
    old_tables = [
        'content_raw',
        'content_processed',
        'exercises',
        'questions'
    ]

    try:
        for table in old_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"[DROPPED] {table}")
            except Exception as e:
                print(f"[SKIP] {table}: {e}")

        conn.commit()
        print("\n[OK] Old tables cleaned up!")

        # Show remaining tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\nRemaining tables ({len(tables)}):")
        for t in tables:
            print(f"  - {t[0]}")

    except Exception as e:
        print(f"[ERROR] {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_old_tables()
