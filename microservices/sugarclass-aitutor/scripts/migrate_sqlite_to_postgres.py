"""
Migrate data from SQLite rag_content.db to PostgreSQL tutor_content
"""
import sqlite3
import asyncio
import asyncpg
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - use environment variables with fallback
# SQLITE_SOURCE_PATH can be either a directory or full path to .db file
sqlite_source = os.getenv("SQLITE_SOURCE_PATH", os.getenv("CONTENT_SOURCE_PATH", ""))
if sqlite_source and sqlite_source.endswith('.db'):
    SQLITE_DB_PATH = sqlite_source
elif sqlite_source:
    SQLITE_DB_PATH = os.path.join(sqlite_source, "rag_content.db")
else:
    # Fallback to /app/content/rag_content.db for container or local path
    SQLITE_DB_PATH = "/app/content/rag_content.db"
    # If that doesn't exist, try old path
    if not os.path.exists(SQLITE_DB_PATH):
        SQLITE_DB_PATH = r"C:\Users\gmhome\SynologyDrive\coding\tutorrag\database\rag_content.db"

logger.info(f"SQLite source env var: {sqlite_source}")
logger.info(f"SQLite database path: {SQLITE_DB_PATH}")

POSTGRES_URL = os.getenv(
    "CONTENT_DB_URL",
    "postgresql://tutor:tutor_content_pass@localhost:5433/tutor_content"
)

import re

def strip_html_tags(text: str) -> str:
    """Strip HTML tags from text and normalize whitespace."""
    if not text:
        return ""
    # Remove script and style elements
    text = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape common HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Read from SQLite
    logger.info(f"Reading from SQLite: {SQLITE_DB_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get syllabuses
    sqlite_cursor.execute("SELECT * FROM syllabuses")
    syllabuses = [dict(row) for row in sqlite_cursor.fetchall()]
    logger.info(f"Found {len(syllabuses)} syllabuses")
    
    # Check topics schema
    sqlite_cursor.execute("PRAGMA table_info(topics)")
    topics_schema = sqlite_cursor.fetchall()
    logger.info(f"Topics schema: {[col[1] for col in topics_schema]}")
    
    # Check content_processed schema
    sqlite_cursor.execute("PRAGMA table_info(content_processed)")
    content_schema = sqlite_cursor.fetchall()
    logger.info(f"Content_processed schema: {[col[1] for col in content_schema]}")
    
    # Check subtopics schema
    sqlite_cursor.execute("PRAGMA table_info(subtopics)")
    subtopics_schema = sqlite_cursor.fetchall()
    logger.info(f"Subtopics schema: {[col[1] for col in subtopics_schema]}")
    
    # Connect to PostgreSQL
    logger.info("Connecting to PostgreSQL...")
    pg_conn = await asyncpg.connect(POSTGRES_URL)
    
    try:
        logger.info("Migrating content data...")
        
        # Get subjects
        sqlite_cursor.execute("""
            SELECT s.*, syll.name as syllabus_name 
            FROM subjects s 
            JOIN syllabuses syll ON s.syllabus_id = syll.id
        """)
        subjects = [dict(row) for row in sqlite_cursor.fetchall()]
        logger.info(f"Found {len(subjects)} subjects")
        
        # Get topics - no direct content, content is in subtopics
        sqlite_cursor.execute("""
            SELECT 
                t.*,
                sub.name as subject_name,
                syl.name as syllabus_name,
                sub.syllabus_id
            FROM topics t
            JOIN subjects sub ON t.subject_id = sub.id
            JOIN syllabuses syl ON sub.syllabus_id = syl.id
        """)
        topics = [dict(row) for row in sqlite_cursor.fetchall()]
        logger.info(f"Found {len(topics)} topics")
        
        # Get subtopics
        sqlite_cursor.execute("""
            SELECT 
                st.id,
                st.name as title,
                st.topic_id,
                t.name as topic_title,
                sub.name as subject_name,
                syl.name as syllabus_name
            FROM subtopics st
            JOIN topics t ON st.topic_id = t.id
            JOIN subjects sub ON t.subject_id = sub.id
            JOIN syllabuses syl ON sub.syllabus_id = syl.id
        """)
        subtopics = [dict(row) for row in sqlite_cursor.fetchall()]
        logger.info(f"Found {len(subtopics)} subtopics")
        
        # Insert into syllabus_hierarchy
        inserted_count = 0
        for topic in topics:
            subject_name = topic.get('subject_name')
            syllabus_name = topic.get('syllabus_name')
            topic_name = topic.get('name', 'General')
            content = strip_html_tags(topic.get('processed_content') or topic_name)
            
            # Create a structured entry - use topic name as chapter
            # Generate synthetic file path since SQLite data doesn't have it
            file_path = f"migrated/{syllabus_name}/{subject_name}/{topic_name}.md"
            
            try:
                await pg_conn.execute("""
                    INSERT INTO syllabus_hierarchy (
                        syllabus, subject, chapter, subtopic,
                        content_type, file_path, markdown_content, word_count, difficulty_level
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (syllabus, subject, chapter, subtopic, content_type) 
                    DO UPDATE SET markdown_content = EXCLUDED.markdown_content
                """, 
                    syllabus_name or 'Unknown',
                    subject_name or 'Unknown',
                    topic_name,
                    'Overview',
                    'textbook',
                    file_path,
                    content,
                    len(content.split()) if content else 0,
                    'core'
                )
                inserted_count += 1
            except asyncpg.exceptions.UniqueViolationError:
                pass  # Skip duplicates
        
        logger.info(f"Inserted {inserted_count} topic records into syllabus_hierarchy")
        
        # Get subtopic content
        for subtopic in subtopics:
            sqlite_cursor.execute("""
                SELECT html_content, summary 
                FROM content_processed 
                WHERE subtopic_id = ?
            """, (subtopic['id'],))
            content_data = sqlite_cursor.fetchone()
            
            if content_data:
                content = strip_html_tags(content_data[0] or content_data[1] or subtopic.get('title', ''))
                
                # Generate synthetic file path
                file_path = f"migrated/{subtopic.get('syllabus_name', 'Unknown')}/{subtopic.get('subject_name', 'Unknown')}/{subtopic.get('topic_title', 'General')}/{subtopic.get('title', 'Content')}.md"
                
                try:
                    await pg_conn.execute("""
                        INSERT INTO syllabus_hierarchy (
                            syllabus, subject, chapter, subtopic,
                            content_type, file_path, markdown_content, word_count, difficulty_level
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (syllabus, subject, chapter, subtopic, content_type) 
                        DO UPDATE SET markdown_content = EXCLUDED.markdown_content
                    """, 
                        subtopic.get('syllabus_name', 'Unknown'),
                        subtopic.get('subject_name', 'Unknown'),
                        subtopic.get('topic_title', 'General'),
                        subtopic.get('title', 'Content'),
                        'textbook',
                        file_path,
                        content,
                        len(content.split()) if content else 0,
                        'core'
                    )
                    inserted_count += 1
                except asyncpg.exceptions.UniqueViolationError:
                    pass  # Skip duplicates
        
        # Check final count
        count = await pg_conn.fetchval("SELECT COUNT(*) FROM syllabus_hierarchy")
        logger.info(f"Total records in syllabus_hierarchy: {count}")
        
        await pg_conn.close()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
