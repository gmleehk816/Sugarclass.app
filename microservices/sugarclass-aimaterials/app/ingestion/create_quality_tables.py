#!/usr/bin/env python3
"""
Create quality tracking tables for ingestion and rewriting processes.

This script adds two new tables to the database:
1. ingestion_quality - Track raw content injection quality
2. rewriting_quality - Track HTML rewrite quality
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent.parent / 'database' / 'rag_content.db')


def create_quality_tables():
    """Create quality tracking tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("Creating Quality Tracking Tables")
    print("=" * 80)
    print()
    
    # Check if tables already exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('ingestion_quality', 'rewriting_quality')
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    if 'ingestion_quality' in existing_tables:
        print("✓ ingestion_quality table already exists")
    else:
        print("Creating ingestion_quality table...")
        cursor.execute("""
            CREATE TABLE ingestion_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subtopic_id TEXT NOT NULL,
                subject_name TEXT,
                status TEXT CHECK(status IN ('pending', 'ingested', 'failed', 'needs_review')) DEFAULT 'pending',
                ingested_at TIMESTAMP,
                quality_score REAL CHECK(quality_score >= 0 AND quality_score <= 100),
                content_length INTEGER,
                content_valid INTEGER CHECK(content_valid IN (0,1)) DEFAULT 0,
                error_message TEXT,
                FOREIGN KEY (subtopic_id) REFERENCES subtopics(id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_ingestion_status ON ingestion_quality(status)
        """)
        cursor.execute("""
            CREATE INDEX idx_ingestion_subject ON ingestion_quality(subject_name)
        """)
        cursor.execute("""
            CREATE INDEX idx_ingestion_subtopic ON ingestion_quality(subtopic_id)
        """)
        
        print("  ✓ ingestion_quality table created")
        print("  ✓ Indexes created")
    
    print()
    
    if 'rewriting_quality' in existing_tables:
        print("✓ rewriting_quality table already exists")
    else:
        print("Creating rewriting_quality table...")
        cursor.execute("""
            CREATE TABLE rewriting_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subtopic_id TEXT NOT NULL,
                subject_name TEXT,
                status TEXT CHECK(status IN ('pending', 'rewritten', 'failed', 'needs_review')) DEFAULT 'pending',
                rewritten_at TIMESTAMP,
                quality_score REAL CHECK(quality_score >= 0 AND quality_score <= 100),
                raw_length INTEGER,
                processed_length INTEGER,
                compression_ratio REAL,
                has_learning_objectives INTEGER DEFAULT 0,
                has_key_terms INTEGER DEFAULT 0,
                has_questions INTEGER DEFAULT 0,
                has_takeaways INTEGER DEFAULT 0,
                error_message TEXT,
                processor_version TEXT,
                FOREIGN KEY (subtopic_id) REFERENCES subtopics(id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_rewriting_status ON rewriting_quality(status)
        """)
        cursor.execute("""
            CREATE INDEX idx_rewriting_subject ON rewriting_quality(subject_name)
        """)
        cursor.execute("""
            CREATE INDEX idx_rewriting_subtopic ON rewriting_quality(subtopic_id)
        """)
        
        print("  ✓ rewriting_quality table created")
        print("  ✓ Indexes created")
    
    conn.commit()
    
    print()
    print("=" * 80)
    print("✓ Quality tracking tables setup complete!")
    print("=" * 80)
    print()
    
    # Show table structure
    print("Table Structures:")
    print()
    print("ingestion_quality:")
    cursor.execute("PRAGMA table_info(ingestion_quality)")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
    print()
    print("rewriting_quality:")
    cursor.execute("PRAGMA table_info(rewriting_quality)")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    
    print()
    print("✓ Database enhanced successfully!")


if __name__ == "__main__":
    create_quality_tables()