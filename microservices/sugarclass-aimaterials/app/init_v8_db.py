#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V8 Migration Script - Adds V8 tables to existing database
Run this script to add V8 tables without dropping existing data.
"""
import sqlite3
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Get paths
SCRIPT_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DB_PATH", SCRIPT_DIR / "database" / "rag_content.db"))

def migrate_to_v8():
    """Add V8 tables to existing database without dropping data."""
    print(f"[V8 Migration] Database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"[V8 Migration] Database not found!")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing V8 tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'v8_%'")
    existing = [t[0] for t in cursor.fetchall()]
    if existing:
        print(f"[V8 Migration] V8 tables already exist: {existing}")
        conn.close()
        return True

    print("[V8 Migration] Creating V8 tables...")

    # V8-specific table creation statements
    v8_tables_sql = [
        # V8 Concepts
        """CREATE TABLE IF NOT EXISTS v8_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            concept_key TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            order_num INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
            UNIQUE(subtopic_id, concept_key)
        )""",

        # V8 Generated Content
        """CREATE TABLE IF NOT EXISTS v8_generated_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            content TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (concept_id) REFERENCES v8_concepts(id) ON DELETE CASCADE
        )""",

        # V8 Quiz Questions
        """CREATE TABLE IF NOT EXISTS v8_quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            question_num INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options JSON NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            difficulty TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
            UNIQUE(subtopic_id, question_num)
        )""",

        # V8 Flashcards
        """CREATE TABLE IF NOT EXISTS v8_flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            card_num INTEGER NOT NULL,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
            UNIQUE(subtopic_id, card_num)
        )""",

        # V8 Real-Life Images
        """CREATE TABLE IF NOT EXISTS v8_reallife_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            image_type TEXT NOT NULL,
            image_url TEXT NOT NULL,
            prompt TEXT,
            title TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE,
            UNIQUE(subtopic_id, image_type)
        )""",

        # V8 Learning Objectives
        """CREATE TABLE IF NOT EXISTS v8_learning_objectives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            objective_text TEXT NOT NULL,
            order_num INTEGER DEFAULT 0,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        )""",

        # V8 Key Terms
        """CREATE TABLE IF NOT EXISTS v8_key_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            definition TEXT,
            order_num INTEGER DEFAULT 0,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        )""",

        # V8 Formulas
        """CREATE TABLE IF NOT EXISTS v8_formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            formula TEXT NOT NULL,
            description TEXT,
            order_num INTEGER DEFAULT 0,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        )""",

        # V8 Processing Tasks
        """CREATE TABLE IF NOT EXISTS v8_processing_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL UNIQUE,
            subtopic_id INTEGER,
            task_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            message TEXT,
            error TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE SET NULL
        )""",

        # V8 Task Logs
        """CREATE TABLE IF NOT EXISTS v8_task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            log_level TEXT DEFAULT 'info',
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES v8_processing_tasks(task_id) ON DELETE CASCADE
        )""",
    ]

    # Create indexes
    v8_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_v8_concepts_subtopic ON v8_concepts(subtopic_id)",
        "CREATE INDEX IF NOT EXISTS idx_v8_generated_content_concept ON v8_generated_content(concept_id)",
        "CREATE INDEX IF NOT EXISTS idx_v8_generated_content_type ON v8_generated_content(content_type)",
        "CREATE INDEX IF NOT EXISTS idx_v8_quiz_subtopic ON v8_quiz_questions(subtopic_id)",
        "CREATE INDEX IF NOT EXISTS idx_v8_flashcards_subtopic ON v8_flashcards(subtopic_id)",
        "CREATE INDEX IF NOT EXISTS idx_v8_reallife_subtopic ON v8_reallife_images(subtopic_id)",
        "CREATE INDEX IF NOT EXISTS idx_v8_tasks_status ON v8_processing_tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_v8_tasks_subtopic ON v8_processing_tasks(subtopic_id)",
    ]

    try:
        # Create tables
        for sql in v8_tables_sql:
            cursor.execute(sql)

        # Create indexes
        for sql in v8_indexes_sql:
            cursor.execute(sql)

        # Add V8 columns to subtopics if they don't exist
        cursor.execute("PRAGMA table_info(subtopics)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'processed_at' not in columns:
            cursor.execute("ALTER TABLE subtopics ADD COLUMN processed_at TIMESTAMP")
            print("[V8 Migration] Added processed_at column to subtopics")

        if 'source_hash' not in columns:
            cursor.execute("ALTER TABLE subtopics ADD COLUMN source_hash TEXT")
            print("[V8 Migration] Added source_hash column to subtopics")

        if 'markdown_file_path' not in columns:
            cursor.execute("ALTER TABLE subtopics ADD COLUMN markdown_file_path TEXT")
            print("[V8 Migration] Added markdown_file_path column to subtopics")

        conn.commit()

        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'v8_%'")
        v8_tables = [t[0] for t in cursor.fetchall()]
        print(f"[V8 Migration] Created {len(v8_tables)} V8 tables: {v8_tables}")

        conn.close()
        return True

    except Exception as e:
        print(f"[V8 Migration] Error: {e}")
        conn.rollback()
        conn.close()
        return False


if __name__ == "__main__":
    success = migrate_to_v8()
    sys.exit(0 if success else 1)
