"""
Content Splitter
================
Splits large markdown files into chapters and subtopics, stores in SQLite.

Pipeline:
1. Read large markdown from MinerU output
2. Detect chapter headings (B1, B2, C1, P1, etc.)
3. Detect subtopic headings (B1.01, B1.02, etc.)
4. Store each chunk in SQLite with metadata

Usage:
    python content_splitter.py --file <markdown_path>
    python content_splitter.py --list   # Show available markdown files
"""

import os
import re
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Paths
APP_DIR = Path(__file__).parent.parent
PROJECT_ROOT = APP_DIR.parent
DB_PATH = APP_DIR / "rag_content.db"  # Database in app/ folder
OUTPUT_DIR = PROJECT_ROOT / "output"


def init_database():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    
    # Syllabuses table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS syllabuses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Subjects table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id TEXT PRIMARY KEY,
            syllabus_id TEXT NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (syllabus_id) REFERENCES syllabuses(id)
        )
    """)
    
    # Topics table (B1, B2, C1, P1, etc.)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT,  -- Biology, Chemistry, Physics
            order_num INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)
    
    # Subtopics table (B1.01, B1.02, etc.)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subtopics (
            id TEXT PRIMARY KEY,
            topic_id TEXT NOT NULL,
            name TEXT NOT NULL,
            page INTEGER,
            order_num INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    # Content RAW table (original markdown chunks)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id TEXT NOT NULL,
            title TEXT,
            markdown_content TEXT NOT NULL,
            source_file TEXT,
            char_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id)
        )
    """)
    
    # Content PROCESSED table (rewritten/enhanced)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_processed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id INTEGER NOT NULL,
            subtopic_id TEXT NOT NULL,
            html_content TEXT,
            summary TEXT,
            key_terms TEXT,  -- JSON array
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processor_version TEXT,
            FOREIGN KEY (raw_id) REFERENCES content_raw(id),
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id)
        )
    """)
    
    # Content IMAGES table (AI generated images)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            subtopic_id TEXT,
            image_url TEXT,
            image_path TEXT,
            prompt TEXT,
            concept TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content_processed(id),
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id)
        )
    """)
    
    # Questions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id TEXT,
            topic_id TEXT,
            question_text TEXT NOT NULL,
            question_type TEXT,  -- mcq, short_answer, essay
            options TEXT,  -- JSON for MCQ options
            correct_answer TEXT,
            explanation TEXT,
            difficulty INTEGER,  -- 1-5
            source TEXT,  -- textbook, past_paper, ai_generated
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id),
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")


class ContentSplitter:
    """Split markdown content into chapters and subtopics"""
    
    # Patterns for IGCSE science content
    TOPIC_PATTERN = r'^#\s*(B\d+|C\d+|P\d+)\s+(.+?)(?:\s+\d+)?$'  # # B1 Cells 1
    SUBTOPIC_PATTERN = r'^(B\d+\.\d+|C\d+\.\d+|P\d+\.\d+)\s+(.+?)(?:\s+\d+)?$'  # B1.01 Characteristics...
    
    # Patterns for Maths content (e.g., "# 26 SEQUENCES 533", "A Number sequences 534")
    MATH_TOPIC_PATTERN = r'^#\s*(\d{1,3})\s+(.+?)(?:\s+\d+)?$'
    # Fallback: any single-# heading becomes next chapter in order
    MATH_TOPIC_FALLBACK = r'^#\s+(.+)$'
    MATH_SUBTOPIC_PATTERN = r'^([A-Z])\s+(.+?)(?:\s+\d+)?$'
    
    def __init__(self, syllabus_id: str = "cie_igcse", subject_id: str = "combined_science"):
        self.syllabus_id = syllabus_id
        self.subject_id = subject_id
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
    
    def split_markdown(self, markdown_path: Path) -> Dict:
        """
        Split a markdown file into topics and subtopics.
        
        Returns:
            Dict with split results and statistics
        """
        print(f"📖 Reading: {markdown_path.name}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Results
        topics = {}
        subtopics = {}
        current_topic = None
        current_subtopic = None
        current_content = []
        math_subtopic_counters = {}
        math_chapter_counter = 0
        contents_mode = False
        
        for i, line in enumerate(lines):
            # Check for topic heading (# B1 Cells)
            topic_match = re.match(self.TOPIC_PATTERN, line, re.IGNORECASE)
            math_topic_match = re.match(self.MATH_TOPIC_PATTERN, line)
            # Fallback: only use generic fallback once we've already started encountering numeric chapters
            math_topic_fallback = None
            if not math_topic_match and math_chapter_counter > 0:
                math_topic_fallback = re.match(self.MATH_TOPIC_FALLBACK, line)
            if topic_match:
                # Save previous subtopic content
                if current_subtopic and current_content:
                    subtopics[current_subtopic]['content'] = '\n'.join(current_content)
                    current_content = []
                
                topic_id = topic_match.group(1).upper()
                topic_name = topic_match.group(2).strip()
                
                # Determine type
                topic_type = 'Biology' if topic_id.startswith('B') else \
                             'Chemistry' if topic_id.startswith('C') else 'Physics'
                
                topics[topic_id] = {
                    'id': topic_id,
                    'name': topic_name,
                    'type': topic_type,
                    'line': i
                }
                current_topic = topic_id
                current_subtopic = None
                print(f"   📚 Topic: {topic_id} - {topic_name}")
                continue
            elif math_topic_match or math_topic_fallback:
                # Save previous subtopic content
                if current_subtopic and current_content:
                    subtopics[current_subtopic]['content'] = '\n'.join(current_content)
                    current_content = []
                math_chapter_counter += 1
                if math_topic_match:
                    topic_name = math_topic_match.group(2).strip()
                else:
                    topic_name = math_topic_fallback.group(1).strip()
                topic_num = math_chapter_counter
                topic_id = f"Ch{topic_num}"
                
                topics[topic_id] = {
                    'id': topic_id,
                    'name': topic_name,
                    'type': 'Mathematics',
                    'line': i,
                    'order': topic_num
                }
                current_topic = topic_id
                current_subtopic = None
                math_subtopic_counters[topic_id] = 0
                print(f"   📚 Topic: {topic_id} - {topic_name}")
                # reset contents parsing flag when a new chapter starts
                contents_mode = False
                continue
            
            # Check for subtopic (B1.01 Characteristics...)
            subtopic_match = re.match(self.SUBTOPIC_PATTERN, line)
            math_subtopic_match = re.match(self.MATH_SUBTOPIC_PATTERN, line)
            if subtopic_match:
                # Save previous subtopic content
                if current_subtopic and current_content:
                    subtopics[current_subtopic]['content'] = '\n'.join(current_content)
                    current_content = []
                
                subtopic_id = subtopic_match.group(1).upper()
                subtopic_name = subtopic_match.group(2).strip()
                
                # Infer topic from subtopic ID
                inferred_topic = subtopic_id.split('.')[0]
                if inferred_topic not in topics:
                    topics[inferred_topic] = {
                        'id': inferred_topic,
                        'name': f"Topic {inferred_topic}",
                        'type': 'Biology' if inferred_topic.startswith('B') else \
                                'Chemistry' if inferred_topic.startswith('C') else 'Physics',
                        'line': i
                    }
                
                subtopics[subtopic_id] = {
                    'id': subtopic_id,
                    'topic_id': inferred_topic,
                    'name': subtopic_name,
                    'line': i,
                    'content': ''
                }
                current_subtopic = subtopic_id
                current_topic = inferred_topic
                print(f"      📄 Subtopic: {subtopic_id} - {subtopic_name}")
                continue
            elif math_subtopic_match and current_topic and (current_topic.startswith("M") or current_topic.startswith("Ch")):
                # Save previous subtopic content
                if current_subtopic and current_content:
                    subtopics[current_subtopic]['content'] = '\n'.join(current_content)
                    current_content = []
                
                letter = math_subtopic_match.group(1)
                subtopic_name = math_subtopic_match.group(2).strip()
                subtopic_id = f"{current_topic}.{letter}"
                
                math_subtopic_counters[current_topic] = math_subtopic_counters.get(current_topic, 0) + 1
                
                subtopics[subtopic_id] = {
                    'id': subtopic_id,
                    'topic_id': current_topic,
                    'name': subtopic_name,
                    'line': i,
                    'order': math_subtopic_counters[current_topic],
                    'content': ''
                }
                current_subtopic = subtopic_id
                print(f"      📄 Subtopic: {subtopic_id} - {subtopic_name}")
                continue
            
            # Detect a "Contents:" block inside a math chapter and pre-create lettered subtopics
            if current_topic and current_topic.startswith("Ch"):
                # start contents mode
                if re.match(r'^\s*Contents\s*:\s*$', line, flags=re.I):
                    contents_mode = True
                    continue
                if contents_mode:
                    # end contents mode when encountering empty line or next chapter/topic
                    if not line.strip() or line.strip().startswith('#') or re.match(self.TOPIC_PATTERN, line, re.IGNORECASE):
                        contents_mode = False
                        # fall through to allow outer logic to process this line
                    else:
                        m = re.match(r'^\s*([A-Z])[\.\)\-]?\s+(.+?)(?:\s+\[\d+\])?\s*$', line)
                        if m:
                            letter = m.group(1)
                            title = m.group(2).strip()
                            subtopic_id = f"{current_topic}.{letter}"
                            if subtopic_id not in subtopics:
                                math_subtopic_counters[current_topic] = math_subtopic_counters.get(current_topic, 0) + 1
                                subtopics[subtopic_id] = {
                                    'id': subtopic_id,
                                    'topic_id': current_topic,
                                    'name': title,
                                    'line': i,
                                    'order': math_subtopic_counters[current_topic],
                                    'content': ''
                                }
                                print(f"      📄 (Contents) Subtopic: {subtopic_id} - {title}")
                            continue
            
            # Accumulate content for current subtopic
            if current_subtopic:
                current_content.append(line)
        
        # Save last subtopic
        if current_subtopic and current_content:
            subtopics[current_subtopic]['content'] = '\n'.join(current_content)
        
        return {
            'source_file': str(markdown_path),
            'topics': topics,
            'subtopics': subtopics,
            'stats': {
                'total_topics': len(topics),
                'total_subtopics': len(subtopics),
                'total_chars': len(content)
            }
        }
    
    def store_in_database(self, split_result: Dict) -> Dict:
        """Store split content in SQLite database"""
        
        # Ensure syllabus exists
        self.conn.execute(
            "INSERT OR IGNORE INTO syllabuses (id, name) VALUES (?, ?)",
            (self.syllabus_id, self.syllabus_id.replace('_', ' ').title())
        )
        
        # Ensure subject exists
        self.conn.execute(
            "INSERT OR IGNORE INTO subjects (id, syllabus_id, name) VALUES (?, ?, ?)",
            (self.subject_id, self.syllabus_id, self.subject_id.replace('_', ' ').title())
        )
        
        # Store topics
        for topic_id, topic in split_result['topics'].items():
            full_topic_id = f"{self.subject_id}_{topic_id}"
            self.conn.execute("""
                INSERT OR REPLACE INTO topics (id, subject_id, name, type, order_num)
                VALUES (?, ?, ?, ?, ?)
            """, (full_topic_id, self.subject_id, topic['name'], topic['type'], topic.get('order', topic.get('line', 0))))
        
        # Store subtopics and raw content
        stored_count = 0
        for subtopic_id, subtopic in split_result['subtopics'].items():
            full_subtopic_id = f"{self.subject_id}_{subtopic_id}"
            full_topic_id = f"{self.subject_id}_{subtopic['topic_id']}"
            
            # Store subtopic
            self.conn.execute("""
                INSERT OR REPLACE INTO subtopics (id, topic_id, name, order_num)
                VALUES (?, ?, ?, ?)
            """, (full_subtopic_id, full_topic_id, subtopic['name'], subtopic.get('order', subtopic.get('line', 0))))
            
            # Store raw content
            content = subtopic.get('content', '')
            if content.strip():
                self.conn.execute("""
                    INSERT INTO content_raw (subtopic_id, title, markdown_content, source_file, char_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (full_subtopic_id, subtopic['name'], content, split_result['source_file'], len(content)))
                stored_count += 1
        
        self.conn.commit()
        
        return {
            'topics_stored': len(split_result['topics']),
            'subtopics_stored': len(split_result['subtopics']),
            'content_chunks_stored': stored_count
        }
    
    def process_file(self, markdown_path: Path) -> Dict:
        """Full pipeline: split and store"""
        split_result = self.split_markdown(markdown_path)
        store_result = self.store_in_database(split_result)
        
        return {
            **split_result['stats'],
            **store_result
        }
    
    def close(self):
        self.conn.close()


def get_database_stats() -> Dict:
    """Get current database statistics"""
    conn = sqlite3.connect(DB_PATH)
    
    stats = {}
    tables = ['syllabuses', 'subjects', 'topics', 'subtopics', 'content_raw', 'content_processed', 'questions']
    
    for table in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = count
        except:
            stats[table] = 0
    
    conn.close()
    return stats


def list_available_markdown():
    """List markdown files available for processing"""
    md_files = []
    
    for md_file in OUTPUT_DIR.rglob("*.md"):
        if "enhanced" in str(md_file) or "original" in str(md_file):
            continue
        
        size_kb = md_file.stat().st_size / 1024
        if size_kb > 10:  # Only show files > 10KB (real content)
            md_files.append({
                'path': md_file,
                'name': md_file.stem,
                'size_kb': round(size_kb, 1)
            })
    
    return sorted(md_files, key=lambda x: -x['size_kb'])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Split markdown into chapters and store in SQLite")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--list", action="store_true", help="List available markdown files")
    parser.add_argument("--file", type=str, help="Process a specific markdown file")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--syllabus", type=str, default="cie_igcse", help="Syllabus ID")
    parser.add_argument("--subject", type=str, default="combined_science", help="Subject ID")
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
    
    if args.stats:
        print("\n📊 Database Statistics:")
        stats = get_database_stats()
        for table, count in stats.items():
            print(f"   {table}: {count} rows")
    
    if args.list:
        print("\n📚 Available Markdown Files (>10KB):")
        files = list_available_markdown()
        for i, f in enumerate(files, 1):
            print(f"   [{i}] {f['name'][:50]}... ({f['size_kb']} KB)")
            print(f"       {f['path']}")
    
    if args.file:
        # Initialize DB if needed
        init_database()
        
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            exit(1)
        
        print(f"\n🔄 Processing: {file_path.name}")
        print(f"   Syllabus: {args.syllabus}")
        print(f"   Subject: {args.subject}")
        print("-" * 50)
        
        splitter = ContentSplitter(args.syllabus, args.subject)
        result = splitter.process_file(file_path)
        splitter.close()
        
        print("\n✅ Results:")
        print(json.dumps(result, indent=2))
        
        print("\n📊 Database Statistics:")
        stats = get_database_stats()
        for table, count in stats.items():
            print(f"   {table}: {count} rows")
