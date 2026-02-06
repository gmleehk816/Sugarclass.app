"""
Enhanced Quality Report Ingestor V2 (TITLE-BASED + FUZZY MATCHING)
==================================================================
Improved ingestion pipeline with:
- Fuzzy title matching for edge cases
- Content length validation
- Image path tracking
- Progress tracking and resume capability
- Better error handling with retries
- Content checksums for change detection

Workflow:
1. Scan materials_output for *_quality_report.json files
2. Read each quality report directly
3. Find corresponding .md file
4. Extract chapters and subtopics with FUZZY TITLE MATCHING
5. Track images referenced in content
6. Validate content extraction quality
7. Insert into database with checksums

Author: Enhanced workflow (v2.0)
Date: 2026-01-12
"""
import json
import sqlite3
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from datetime import datetime
import traceback

# Path configuration
DB_PATH = Path(__file__).parent.parent / 'database' / 'rag_content.db'
OUTPUT_DIR = Path(r'e:\SynologyDrive\coding\tutorsystem\output\materials_output')
PROGRESS_FILE = Path(__file__).parent.parent / 'database' / 'ingestion_progress.json'

# Minimum content length thresholds
MIN_CONTENT_LENGTH = 100  # Characters
MIN_CONTENT_RATIO = 0.1   # Minimum ratio vs markdown file size


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def sanitize_id(name: str) -> str:
    """Create a safe ID from a name"""
    id_clean = re.sub(r'[^\w\s-]', '', name)
    id_clean = re.sub(r'[-\s]+', '_', id_clean)
    return id_clean.lower().strip('_')[:100]  # Limit length


def compute_content_hash(content: str) -> str:
    """Compute MD5 hash of content for change detection"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def fuzzy_find_title(content: str, title: str, threshold: float = 0.75) -> Optional[int]:
    """
    Find title in content using fuzzy matching.
    Returns the position of best match or None if no match above threshold.
    
    Args:
        content: The full markdown content
        title: The title to search for
        threshold: Minimum similarity ratio (0-1)
    
    Returns:
        Position in content or None
    """
    content_lower = content.lower()
    title_lower = title.lower().strip()
    
    # 1. Try exact match first (fastest)
    exact_pos = content_lower.find(title_lower)
    if exact_pos != -1:
        return exact_pos
    
    # 2. Try with normalized whitespace
    title_normalized = ' '.join(title_lower.split())
    content_normalized_map = {}
    
    # 3. Try matching each line for headers (common case)
    lines = content.split('\n')
    pos = 0
    best_match = None
    best_ratio = 0
    
    for line in lines:
        line_stripped = line.strip().lower()
        
        # Skip empty lines
        if not line_stripped:
            pos += len(line) + 1
            continue
        
        # Remove markdown header markers for comparison
        line_clean = re.sub(r'^#+\s*', '', line_stripped)
        line_clean = re.sub(r'^[\d\.]+\s*', '', line_clean)  # Remove numbering
        
        # Calculate similarity
        ratio = SequenceMatcher(None, title_normalized, line_clean).ratio()
        
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = pos
        
        pos += len(line) + 1
    
    if best_match is not None:
        return best_match
    
    # 4. Sliding window approach for embedded titles
    window_size = len(title_lower) + 20  # Allow some extra chars
    
    for i in range(0, len(content_lower) - window_size + 1, 50):  # Step by 50 chars
        window = content_lower[i:i + window_size]
        
        ratio = SequenceMatcher(None, title_lower, window).ratio()
        
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = i
    
    return best_match


def extract_image_references(content: str, base_path: Path) -> List[Dict]:
    """
    Extract all image references from markdown content.
    
    Returns:
        List of dicts with image info: {path, alt_text, exists}
    """
    images = []
    
    # Match markdown image syntax: ![alt](path)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    for match in re.finditer(pattern, content):
        alt_text = match.group(1)
        img_path = match.group(2)
        
        # Resolve relative paths
        if not img_path.startswith(('http://', 'https://', '/')):
            full_path = base_path / img_path
            exists = full_path.exists()
        else:
            full_path = img_path
            exists = None  # Can't check URLs
        
        images.append({
            'alt_text': alt_text,
            'path': img_path,
            'full_path': str(full_path),
            'exists': exists,
            'position': match.start()
        })
    
    return images


def validate_content(content: str, title: str, markdown_size: int) -> Tuple[bool, str]:
    """
    Validate extracted content quality.
    
    Returns:
        (is_valid, message)
    """
    if not content:
        return False, "Empty content"
    
    content_len = len(content)
    
    if content_len < MIN_CONTENT_LENGTH:
        return False, f"Too short ({content_len} chars, min {MIN_CONTENT_LENGTH})"
    
    # Check if content is just the title repeated
    if content.strip().lower() == title.lower():
        return False, "Content is just the title"
    
    # Check for meaningful content (not just whitespace/special chars)
    text_only = re.sub(r'[^\w\s]', '', content)
    if len(text_only.strip()) < MIN_CONTENT_LENGTH // 2:
        return False, "Mostly non-text content"
    
    return True, "Valid"


def parse_book_path(quality_report_path: Path) -> Optional[Dict[str, str]]:
    """
    Extract book information from quality report path.
    
    Expected structure:
    {syllabus}/{subject}/{type}/{book_name}/{book_name}_quality_report.json
    """
    try:
        rel_path = quality_report_path.relative_to(OUTPUT_DIR)
        parts = list(rel_path.parts)
        
        if len(parts) < 4:
            print(f"  ❌ Invalid path structure: {rel_path}")
            return None
        
        syllabus = parts[0]
        subject = parts[1]
        book_type = parts[2]
        
        book_dir = quality_report_path.parent
        
        # Find markdown file
        quality_report_name = quality_report_path.stem.replace('_quality_report', '')
        markdown_file = book_dir / f"{quality_report_name}.md"
        
        # Get markdown file size
        markdown_size = markdown_file.stat().st_size if markdown_file.exists() else 0
        
        return {
            'syllabus': syllabus,
            'subject': subject,
            'type': book_type,
            'book_name': quality_report_name,
            'book_dir': str(book_dir),
            'markdown_file': str(markdown_file) if markdown_file.exists() else None,
            'markdown_size': markdown_size,
            'quality_report': str(quality_report_path)
        }
        
    except Exception as e:
        print(f"  ❌ Error parsing path: {e}")
        return None


def create_subject(conn, subject_name: str, syllabus: str) -> str:
    """Create subject if not exists, return subject_id"""
    existing = conn.execute(
        "SELECT id FROM subjects WHERE name = ?",
        (subject_name,)
    ).fetchone()
    
    if existing:
        return existing['id']
    
    subject_id = sanitize_id(subject_name)
    syllabus_id = sanitize_id(syllabus)
    
    try:
        conn.execute(
            "INSERT INTO subjects (id, name, syllabus_id, code) VALUES (?, ?, ?, ?)",
            (subject_id, subject_name, syllabus_id, syllabus.split()[0] if ' ' in syllabus else syllabus)
        )
        conn.commit()
        print(f"    ✅ Created subject: {subject_name}")
        return subject_id
    except sqlite3.IntegrityError:
        count = conn.execute("SELECT COUNT(*) FROM subjects WHERE id LIKE ?", (f"{subject_id}%",)).fetchone()[0]
        subject_id = f"{subject_id}_{count}"
        conn.execute(
            "INSERT INTO subjects (id, name, syllabus_id, code) VALUES (?, ?, ?, ?)",
            (subject_id, subject_name, syllabus_id, syllabus.split()[0] if ' ' in syllabus else syllabus)
        )
        conn.commit()
        print(f"    ✅ Created subject: {subject_name} (ID: {subject_id})")
        return subject_id


def create_topic(conn, subject_id: str, topic_title: str, order_num: int) -> str:
    """Create topic if not exists, return topic_id"""
    existing = conn.execute(
        "SELECT id FROM topics WHERE subject_id = ? AND name = ?",
        (subject_id, topic_title)
    ).fetchone()
    
    if existing:
        return existing['id']
    
    topic_id = sanitize_id(topic_title)
    full_id = f"{subject_id}_{topic_id}"
    
    try:
        conn.execute(
            "INSERT INTO topics (id, name, subject_id, type, order_num) VALUES (?, ?, ?, ?, ?)",
            (full_id, topic_title, subject_id, 'Chapter', order_num)
        )
        conn.commit()
        return full_id
    except sqlite3.IntegrityError:
        count = conn.execute("SELECT COUNT(*) FROM topics WHERE id LIKE ?", (f"{full_id}%",)).fetchone()[0]
        full_id = f"{subject_id}_{topic_id}_{count}"
        conn.execute(
            "INSERT INTO topics (id, name, subject_id, type, order_num) VALUES (?, ?, ?, ?, ?)",
            (full_id, topic_title, subject_id, 'Chapter', order_num)
        )
        conn.commit()
        return full_id


def create_subtopic(conn, topic_id: str, subtopic_title: str, order_num: int) -> str:
    """Create subtopic if not exists, return subtopic_id"""
    existing = conn.execute(
        "SELECT id FROM subtopics WHERE topic_id = ? AND name = ?",
        (topic_id, subtopic_title)
    ).fetchone()
    
    if existing:
        return existing['id']
    
    subtopic_id = sanitize_id(subtopic_title)
    full_id = f"{topic_id}_{subtopic_id}"
    
    try:
        conn.execute(
            "INSERT INTO subtopics (id, name, topic_id, order_num) VALUES (?, ?, ?, ?)",
            (full_id, subtopic_title, topic_id, order_num)
        )
        conn.commit()
        return full_id
    except sqlite3.IntegrityError:
        count = conn.execute("SELECT COUNT(*) FROM subtopics WHERE id LIKE ?", (f"{full_id}%",)).fetchone()[0]
        full_id = f"{topic_id}_{subtopic_id}_{count}"
        conn.execute(
            "INSERT INTO subtopics (id, name, topic_id, order_num) VALUES (?, ?, ?, ?)",
            (full_id, subtopic_title, topic_id, order_num)
        )
        conn.commit()
        return full_id


def extract_subtopic_content_v2(
    markdown_file: str, 
    title: str, 
    next_title: Optional[str] = None,
    all_titles: Optional[List[str]] = None
) -> Tuple[str, Dict]:
    """
    Enhanced content extraction with fuzzy matching and validation.
    
    Returns:
        Tuple of (content, metadata)
        metadata includes: match_type, match_ratio, position, images
    """
    metadata = {
        'match_type': 'none',
        'match_ratio': 0.0,
        'position': -1,
        'images': [],
        'validation': None
    }
    
    try:
        with open(markdown_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        file_size = len(content)
        base_path = Path(markdown_file).parent
        
        # Find title position using fuzzy matching
        title_pos = fuzzy_find_title(content, title)
        
        if title_pos is None:
            metadata['match_type'] = 'not_found'
            print(f"        ⚠️  Title not found (fuzzy): '{title[:50]}...'")
            return "", metadata
        
        # Determine if exact or fuzzy match
        if content.lower().find(title.lower()) == title_pos:
            metadata['match_type'] = 'exact'
            metadata['match_ratio'] = 1.0
        else:
            metadata['match_type'] = 'fuzzy'
            # Calculate actual match ratio
            window = content[title_pos:title_pos + len(title) + 20].lower()
            metadata['match_ratio'] = SequenceMatcher(None, title.lower(), window).ratio()
        
        metadata['position'] = title_pos
        
        # Find end boundary
        end_pos = len(content)
        
        if next_title:
            next_pos = fuzzy_find_title(content[title_pos + len(title):], next_title)
            if next_pos is not None:
                end_pos = title_pos + len(title) + next_pos
        
        # If no next_title, try to find any other title from the list
        if end_pos == len(content) and all_titles:
            for other_title in all_titles:
                if other_title.lower().strip() == title.lower().strip():
                    continue
                other_pos = fuzzy_find_title(content[title_pos + len(title):], other_title)
                if other_pos is not None:
                    potential_end = title_pos + len(title) + other_pos
                    if potential_end < end_pos:
                        end_pos = potential_end
        
        # Extract content
        extracted = content[title_pos:end_pos].strip()
        
        # Extract image references
        metadata['images'] = extract_image_references(extracted, base_path)
        
        # Validate content
        is_valid, validation_msg = validate_content(extracted, title, file_size)
        metadata['validation'] = {
            'is_valid': is_valid,
            'message': validation_msg,
            'length': len(extracted)
        }
        
        if not is_valid:
            print(f"        ⚠️  Content validation: {validation_msg}")
        
        return extracted, metadata
        
    except Exception as e:
        print(f"      ⚠️  Error extracting content for '{title[:50]}...': {e}")
        metadata['match_type'] = 'error'
        metadata['validation'] = {'is_valid': False, 'message': str(e)}
        return "", metadata


def insert_raw_content_v2(
    conn, 
    subtopic_id: str, 
    title: str, 
    content: str,
    source_file: str,
    extraction_metadata: Dict
) -> int:
    """
    Insert or update raw content with enhanced metadata.
    
    Returns:
        content_raw.id
    """
    content_hash = compute_content_hash(content)
    
    existing = conn.execute(
        "SELECT id, markdown_content FROM content_raw WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()
    
    if existing:
        existing_hash = compute_content_hash(existing['markdown_content']) if existing['markdown_content'] else ''
        
        if existing_hash == content_hash:
            # Content unchanged
            return existing['id']
        
        # Update with new content
        conn.execute("""
            UPDATE content_raw 
            SET markdown_content = ?, 
                title = ?,
                source_file = ?,
                content_hash = ?,
                extraction_method = ?,
                updated_at = datetime('now')
            WHERE subtopic_id = ?
        """, (
            content, 
            title,
            source_file,
            content_hash,
            extraction_metadata.get('match_type', 'unknown'),
            subtopic_id
        ))
        conn.commit()
        return existing['id']
    else:
        # Insert new
        cursor = conn.execute("""
            INSERT INTO content_raw 
            (subtopic_id, title, markdown_content, source_file, content_hash, extraction_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            subtopic_id, 
            title, 
            content,
            source_file,
            content_hash,
            extraction_metadata.get('match_type', 'unknown')
        ))
        conn.commit()
        return cursor.lastrowid


def insert_content_images(conn, raw_id: int, images: List[Dict]):
    """Insert image references for content"""
    for img in images:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO content_images 
                (raw_id, image_path, alt_text, exists_on_disk)
                VALUES (?, ?, ?, ?)
            """, (
                raw_id,
                img['path'],
                img.get('alt_text', ''),
                1 if img.get('exists') else 0
            ))
        except Exception as e:
            # content_images table might not exist or have different schema
            pass
    conn.commit()


def load_progress() -> Dict:
    """Load ingestion progress from file"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'completed_books': [], 'failed_books': [], 'last_run': None}


def save_progress(progress: Dict):
    """Save ingestion progress to file"""
    progress['last_run'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def ingest_book(quality_report_path: Path, conn) -> Tuple[int, int, int, Dict]:
    """
    Ingest a complete book from its quality report.
    
    Returns: (topics_created, subtopics_created, content_inserted, stats)
    """
    stats = {
        'exact_matches': 0,
        'fuzzy_matches': 0,
        'not_found': 0,
        'invalid_content': 0,
        'images_found': 0
    }
    
    # Parse book information
    book_info = parse_book_path(quality_report_path)
    if not book_info:
        print(f"\n❌ Failed to parse: {quality_report_path.name}")
        return 0, 0, 0, stats
    
    print(f"\n{'='*70}")
    print(f"PROCESSING: {book_info['subject']}")
    print(f"Book: {book_info['book_name']}")
    print(f"Size: {book_info['markdown_size'] / 1024 / 1024:.2f} MB")
    print(f"{'='*70}")
    
    # Check markdown file
    if not book_info['markdown_file']:
        print(f"  ❌ Markdown file NOT found: {book_info['book_name']}.md")
        return 0, 0, 0, stats
    
    markdown_file = Path(book_info['markdown_file'])
    print(f"  ✅ Markdown file: {markdown_file.name}")
    
    # Create subject
    subject_id = create_subject(conn, book_info['subject'], book_info['syllabus'])
    
    # Read quality report
    try:
        with open(quality_report_path, 'r', encoding='utf-8') as f:
            quality_data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error reading quality report: {e}")
        return 0, 0, 0, stats
    
    # Extract chapters
    chapters_data = quality_data.get('pdf_toc', {}).get('chapters', [])
    print(f"  ✅ Found {len(chapters_data)} chapters")
    
    if not chapters_data:
        return 0, 0, 0, stats
    
    # Collect all subtopic titles for boundary detection
    all_titles = []
    for chapter in chapters_data:
        for subtopic in chapter.get('subtopics', []):
            all_titles.append(subtopic.get('title', ''))
    
    # Counters
    topics_created = 0
    subtopics_created = 0
    content_inserted = 0
    
    # Process each chapter
    for chapter_data in chapters_data:
        chapter_num = chapter_data.get('chapter_number', topics_created + 1)
        chapter_title = chapter_data.get('title', 'Unknown')
        
        print(f"\n  Chapter {chapter_num}: {chapter_title[:60]}...")
        
        # Create topic
        topic_id = create_topic(conn, subject_id, chapter_title, chapter_num)
        topics_created += 1
        
        # Process subtopics
        subtopics_data = chapter_data.get('subtopics', [])
        
        if not subtopics_data:
            print(f"    ℹ️  No subtopics")
            continue
        
        for i, subtopic_data in enumerate(subtopics_data):
            subtopic_title = subtopic_data.get('title', 'Unknown')
            
            # Create subtopic
            subtopic_id = create_subtopic(conn, topic_id, subtopic_title, i + 1)
            subtopics_created += 1
            
            # Get next title
            next_title = None
            if i + 1 < len(subtopics_data):
                next_title = subtopics_data[i+1].get('title', None)
            
            # Extract content with enhanced method
            content, metadata = extract_subtopic_content_v2(
                book_info['markdown_file'],
                subtopic_title,
                next_title,
                all_titles
            )
            
            # Update stats
            if metadata['match_type'] == 'exact':
                stats['exact_matches'] += 1
            elif metadata['match_type'] == 'fuzzy':
                stats['fuzzy_matches'] += 1
            elif metadata['match_type'] == 'not_found':
                stats['not_found'] += 1
            
            if metadata.get('validation', {}).get('is_valid') == False:
                stats['invalid_content'] += 1
            
            stats['images_found'] += len(metadata.get('images', []))
            
            if content:
                raw_id = insert_raw_content_v2(
                    conn, 
                    subtopic_id, 
                    subtopic_title, 
                    content,
                    book_info['markdown_file'],
                    metadata
                )
                content_inserted += 1
                
                # Insert image references
                if metadata.get('images'):
                    insert_content_images(conn, raw_id, metadata['images'])
                
                status = "✅" if metadata['match_type'] == 'exact' else "🔶"
                print(f"      {status} {subtopic_title[:55]}... ({len(content)} chars)")
            else:
                print(f"      ❌ {subtopic_title[:55]}... (no content)")
    
    print(f"\n  Summary:")
    print(f"    Topics: {topics_created}")
    print(f"    Subtopics: {subtopics_created}")
    print(f"    Content: {content_inserted}")
    print(f"    Match Types: {stats['exact_matches']} exact, {stats['fuzzy_matches']} fuzzy, {stats['not_found']} not found")
    print(f"    Images: {stats['images_found']}")
    
    return topics_created, subtopics_created, content_inserted, stats


def ensure_schema_updates(conn):
    """Ensure database has all enhanced columns"""
    try:
        # Check if columns exist, add if not
        cursor = conn.execute("PRAGMA table_info(content_raw)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'source_file' not in columns:
            conn.execute("ALTER TABLE content_raw ADD COLUMN source_file TEXT")
            print("  ✅ Added source_file column")
        
        if 'content_hash' not in columns:
            conn.execute("ALTER TABLE content_raw ADD COLUMN content_hash TEXT")
            print("  ✅ Added content_hash column")
        
        if 'extraction_method' not in columns:
            conn.execute("ALTER TABLE content_raw ADD COLUMN extraction_method TEXT")
            print("  ✅ Added extraction_method column")
        
        if 'created_at' not in columns:
            conn.execute("ALTER TABLE content_raw ADD COLUMN created_at TEXT")
            print("  ✅ Added created_at column")
        
        if 'updated_at' not in columns:
            conn.execute("ALTER TABLE content_raw ADD COLUMN updated_at TEXT")
            print("  ✅ Added updated_at column")
        
        conn.commit()
    except Exception as e:
        print(f"  ⚠️  Schema update warning: {e}")


def main():
    """Main ingestion process with enhancements"""
    print("\n" + "="*70)
    print("ENHANCED QUALITY REPORT INGESTOR V2")
    print("="*70)
    print("\nFeatures:")
    print("  ✅ Fuzzy title matching for edge cases")
    print("  ✅ Content validation and quality checks")
    print("  ✅ Image reference tracking")
    print("  ✅ Progress tracking and resume capability")
    print("  ✅ Content checksums for change detection")
    print()
    
    # Load progress
    progress = load_progress()
    print(f"Last run: {progress.get('last_run', 'Never')}")
    print(f"Previously completed: {len(progress.get('completed_books', []))} books")
    
    # Find all quality reports
    print("\nScanning for quality reports...")
    quality_reports = list(OUTPUT_DIR.rglob('*_quality_report.json'))
    quality_reports = [r for r in quality_reports if 'CONVERSION_REQUIREMENTS' not in str(r)]
    
    print(f"Found {len(quality_reports)} quality report files\n")
    
    if not quality_reports:
        print("❌ No quality reports found!")
        return
    
    # Connect to database
    conn = get_db_connection()
    
    # Ensure schema updates
    print("Checking database schema...")
    ensure_schema_updates(conn)
    
    # Get current state
    current_subjects = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    current_topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    current_subtopics = conn.execute("SELECT COUNT(*) FROM subtopics").fetchone()[0]
    current_content = conn.execute("SELECT COUNT(*) FROM content_raw").fetchone()[0]
    
    print(f"\nCurrent database state:")
    print(f"  Subjects: {current_subjects}")
    print(f"  Topics: {current_topics}")
    print(f"  Subtopics: {current_subtopics}")
    print(f"  Raw Content: {current_content}")
    
    # Process each book
    total_stats = {
        'topics': 0,
        'subtopics': 0,
        'content': 0,
        'exact_matches': 0,
        'fuzzy_matches': 0,
        'not_found': 0,
        'images_found': 0
    }
    books_processed = 0
    
    for quality_report in sorted(quality_reports):
        book_key = str(quality_report)
        
        # Skip if already completed (optional - comment out to reprocess)
        # if book_key in progress.get('completed_books', []):
        #     print(f"\n⏭️  Skipping (already done): {quality_report.name[:50]}...")
        #     continue
        
        try:
            topics, subtopics, content, stats = ingest_book(quality_report, conn)
            
            total_stats['topics'] += topics
            total_stats['subtopics'] += subtopics
            total_stats['content'] += content
            total_stats['exact_matches'] += stats.get('exact_matches', 0)
            total_stats['fuzzy_matches'] += stats.get('fuzzy_matches', 0)
            total_stats['not_found'] += stats.get('not_found', 0)
            total_stats['images_found'] += stats.get('images_found', 0)
            
            books_processed += 1
            
            # Mark as completed
            if book_key not in progress.get('completed_books', []):
                progress.setdefault('completed_books', []).append(book_key)
            
        except Exception as e:
            print(f"\n❌ ERROR processing {quality_report.name}: {e}")
            traceback.print_exc()
            progress.setdefault('failed_books', []).append(book_key)
            continue
    
    # Save progress
    save_progress(progress)
    
    # Get final state
    final_subjects = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    final_topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    final_subtopics = conn.execute("SELECT COUNT(*) FROM subtopics").fetchone()[0]
    final_content = conn.execute("SELECT COUNT(*) FROM content_raw").fetchone()[0]
    
    conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("INGESTION SUMMARY")
    print("="*70)
    print(f"\n📚 Books processed: {books_processed}/{len(quality_reports)}")
    print(f"\n📊 Content Statistics:")
    print(f"   Topics created: {total_stats['topics']}")
    print(f"   Subtopics created: {total_stats['subtopics']}")
    print(f"   Content inserted: {total_stats['content']}")
    print(f"\n🎯 Match Quality:")
    print(f"   Exact matches: {total_stats['exact_matches']}")
    print(f"   Fuzzy matches: {total_stats['fuzzy_matches']}")
    print(f"   Not found: {total_stats['not_found']}")
    print(f"\n🖼️  Images tracked: {total_stats['images_found']}")
    print(f"\n📈 Database Changes:")
    print(f"   Subjects: {current_subjects} → {final_subjects} (+{final_subjects - current_subjects})")
    print(f"   Topics: {current_topics} → {final_topics} (+{final_topics - current_topics})")
    print(f"   Subtopics: {current_subtopics} → {final_subtopics} (+{final_subtopics - current_subtopics})")
    print(f"   Raw Content: {current_content} → {final_content} (+{final_content - current_content})")
    
    print("\n" + "="*70)
    print("✅ ENHANCED INGESTION COMPLETED")
    print("="*70)
    print("\nNext steps:")
    print("  1. Validate: python scripts/validate_against_quality_reports.py")
    print("  2. Generate HTML: python scripts/rewrite_all_to_html_v2.py")


if __name__ == '__main__':
    main()
