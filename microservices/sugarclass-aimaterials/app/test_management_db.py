import sqlite3
import os
from pathlib import Path
import re

# Simple test script to verify DB operations
DB_PATH = Path("e:/PROGRAMMING/Projects/Sugarclass.app/microservices/sugarclass-aimaterials/app/database/rag_content.db")

def test_db_ops():
    if not DB_PATH.exists():
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # 0a. Create a dummy syllabus
        print("Creating dummy syllabus...")
        cursor.execute("INSERT INTO syllabuses (name, display_name) VALUES ('Test Syllabus', 'Mock Syllabus')")
        syllabus_id = cursor.lastrowid

        # 0b. Create a dummy subject
        print("Creating dummy subject...")
        cursor.execute("INSERT INTO subjects (name, code, syllabus_id, subject_id) VALUES ('Test Subject', 'TS1', ?, 'test_subject_1')", (syllabus_id,))
        subject_id = cursor.lastrowid

        # 1. Create a dummy topic
        print("Creating dummy topic...")
        import uuid
        topic_uid = f"T_{uuid.uuid4().hex[:8]}"
        cursor.execute("INSERT INTO topics (subject_id, topic_id, name, order_num) VALUES (?, ?, 'Test Topic', 999)", (subject_id, topic_uid))
        topic_id = cursor.lastrowid
        
        # 2. Create a dummy subtopic
        print("Creating dummy subtopic...")
        subtopic_uid = f"S_{uuid.uuid4().hex[:8]}"
        cursor.execute("INSERT INTO subtopics (topic_id, subtopic_id, slug, name, order_num) VALUES (?, ?, 'test-subtopic', 'Test Subtopic', 1)", (topic_id, subtopic_uid))
        subtopic_id = cursor.lastrowid
        
        # 3. Create dummy content (to test cascade)
        print("Creating dummy concept...")
        cursor.execute("INSERT INTO v8_concepts (subtopic_id, concept_key, title) VALUES (?, 'test_key', 'Test Concept')", (subtopic_id,))
        concept_id = cursor.lastrowid
        
        conn.commit()
        print(f"Created Topic ID: {topic_id}, Subtopic ID: {subtopic_id}, Concept ID: {concept_id}")

        # 4. Verify rename subtopic
        print("Testing subtopic rename...")
        new_name = "Renamed Subtopic"
        slug = re.sub(r'[^\w\s-]', '', new_name).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        cursor.execute("UPDATE subtopics SET name = ?, slug = ? WHERE id = ?", (new_name, slug, subtopic_id))
        conn.commit()
        
        renamed = cursor.execute("SELECT name, slug FROM subtopics WHERE id = ?", (subtopic_id,)).fetchone()
        print(f"Renamed: {renamed['name']}, Slug: {renamed['slug']}")
        assert renamed['name'] == new_name
        assert renamed['slug'] == "renamed-subtopic"

        # 5. Verify delete subtopic (cascade)
        print("Testing subtopic delete (cascade)...")
        cursor.execute("DELETE FROM subtopics WHERE id = ?", (subtopic_id,))
        conn.commit()
        
        concept = cursor.execute("SELECT COUNT(*) FROM v8_concepts WHERE subtopic_id = ?", (subtopic_id,)).fetchone()[0]
        print(f"Concepts remaining for subtopic: {concept}")
        assert concept == 0

        # 6. Verify delete topic (cascade)
        # Re-create subtopic first
        subtopic_uid_2 = f"S_{uuid.uuid4().hex[:8]}"
        cursor.execute("INSERT INTO subtopics (topic_id, subtopic_id, slug, name, order_num) VALUES (?, ?, 'test-subtopic-2', 'Test Subtopic 2', 2)", (topic_id, subtopic_uid_2))
        s2_id = cursor.lastrowid
        conn.commit()
        
        print("Testing topic delete (cascade)...")
        cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        conn.commit()
        
        subtopic_count = cursor.execute("SELECT COUNT(*) FROM subtopics WHERE topic_id = ?", (topic_id,)).fetchone()[0]
        print(f"Subtopics remaining for topic: {subtopic_count}")
        assert subtopic_count == 0

        print("\nAll DB-level tests passed!")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    test_db_ops()
