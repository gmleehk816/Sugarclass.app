"""
LLM-Powered Content Ingestion Pipeline
======================================
Main script that orchestrates the full ingestion process:
1. Load quality report (chapters, subtopics structure)
2. Load and chunk markdown file
3. For each chapter: extract subtopics using LLM
4. Insert into content_raw database
5. Generate extraction report

Author: TutorRAG Pipeline v2
Date: 2026-01-04

Usage:
    python scripts/ingest_with_llm.py --quality-report "path/to/quality_report.json"
    python scripts/ingest_with_llm.py --quality-report "path/to/quality_report.json" --output-report "report.json"
"""

import argparse
import json
import sqlite3
import sys
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'app' / 'content_builder'))

from content_builder.markdown_chunker import MarkdownChunker, ChapterChunk
from content_builder.llm_content_extractor import LLMContentExtractor, ExtractionResult


# Configuration
DB_PATH = Path(__file__).parent.parent / 'database' / 'rag_content.db'
DEFAULT_OUTPUT_DIR = Path(r'C:\Users\gmhome\SynologyDrive\coding\pdftomarkdown\output\materials_output')


@dataclass
class IngestionStats:
    """Statistics for the ingestion run"""
    quality_report_path: str
    markdown_path: str
    subject_name: str
    total_chapters: int = 0
    chapters_processed: int = 0
    total_subtopics: int = 0
    subtopics_found: int = 0
    subtopics_complete: int = 0
    content_inserted: int = 0
    issues: List[str] = None
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def sanitize_id(name: str) -> str:
    """Create a safe ID from a name"""
    id_clean = re.sub(r'[^\w\s-]', '', name)
    id_clean = re.sub(r'[-\s]+', '_', id_clean)
    return id_clean.lower().strip('_')[:50]


def get_db_connection() -> sqlite3.Connection:
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_book_path(quality_report_path: Path) -> Optional[Dict]:
    """
    Extract book information from quality report path.

    Returns dict with: syllabus, subject, book_name, markdown_file path
    """
    try:
        # Find the markdown file (same directory, same name without _quality_report)
        quality_report_name = quality_report_path.stem.replace('_quality_report', '')
        book_dir = quality_report_path.parent
        markdown_file = book_dir / f"{quality_report_name}.md"

        # Extract subject from path
        parts = list(quality_report_path.parts)

        # Find subject by looking for pattern like "Physics (0625)"
        subject = "Unknown Subject"
        syllabus = "Unknown"

        for i, part in enumerate(parts):
            if '(' in part and ')' in part:  # Likely subject with code
                subject = part
                if i > 0:
                    syllabus = parts[i - 1] if 'igcse' in parts[i-1].lower() or 'gcse' in parts[i-1].lower() else syllabus
                break

        return {
            'syllabus': syllabus,
            'subject': subject,
            'book_name': quality_report_name,
            'book_dir': str(book_dir),
            'markdown_file': str(markdown_file) if markdown_file.exists() else None,
            'quality_report': str(quality_report_path)
        }

    except Exception as e:
        print(f"Error parsing path: {e}")
        return None


def load_quality_report(quality_report_path: Path) -> Optional[Dict]:
    """Load and parse quality report JSON"""
    try:
        with open(quality_report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading quality report: {e}")
        return None


def ensure_subject_exists(conn: sqlite3.Connection, subject_name: str, syllabus: str) -> str:
    """Create subject if not exists, return subject_id"""
    existing = conn.execute(
        "SELECT id FROM subjects WHERE name = ?",
        (subject_name,)
    ).fetchone()

    if existing:
        return existing['id']

    subject_id = sanitize_id(subject_name)

    try:
        conn.execute(
            "INSERT INTO subjects (id, name, syllabus_id, code) VALUES (?, ?, ?, ?)",
            (subject_id, subject_name, sanitize_id(syllabus), syllabus.split()[0] if ' ' in syllabus else syllabus)
        )
        conn.commit()
        print(f"  Created subject: {subject_name}")
        return subject_id
    except sqlite3.IntegrityError:
        # Handle conflict
        count = conn.execute("SELECT COUNT(*) FROM subjects WHERE id LIKE ?", (f"{subject_id}%",)).fetchone()[0]
        subject_id = f"{subject_id}_{count}"
        conn.execute(
            "INSERT INTO subjects (id, name, syllabus_id, code) VALUES (?, ?, ?, ?)",
            (subject_id, subject_name, sanitize_id(syllabus), syllabus.split()[0] if ' ' in syllabus else syllabus)
        )
        conn.commit()
        return subject_id


def ensure_topic_exists(conn: sqlite3.Connection, subject_id: str, topic_title: str, order_num: int) -> str:
    """Create topic if not exists, return topic_id"""
    existing = conn.execute(
        "SELECT id FROM topics WHERE subject_id = ? AND name = ?",
        (subject_id, topic_title)
    ).fetchone()

    if existing:
        return existing['id']

    # Create new topic ID with book prefix for uniqueness
    topic_id = f"book_{subject_id[:2]}_{order_num:02d}"

    try:
        conn.execute(
            "INSERT INTO topics (id, name, subject_id, type, order_num) VALUES (?, ?, ?, ?, ?)",
            (topic_id, topic_title, subject_id, 'Chapter', order_num)
        )
        conn.commit()
        return topic_id
    except sqlite3.IntegrityError:
        # Update existing
        conn.execute(
            "UPDATE topics SET name = ? WHERE id = ?",
            (topic_title, topic_id)
        )
        conn.commit()
        return topic_id


def ensure_subtopic_exists(conn: sqlite3.Connection, topic_id: str, subtopic_title: str, order_num: int) -> str:
    """Create subtopic if not exists, return subtopic_id"""
    existing = conn.execute(
        "SELECT id FROM subtopics WHERE topic_id = ? AND name = ?",
        (topic_id, subtopic_title)
    ).fetchone()

    if existing:
        return existing['id']

    # Create subtopic ID
    subtopic_id = f"subtopic_{topic_id}_{order_num:02d}"

    try:
        conn.execute(
            "INSERT INTO subtopics (id, name, topic_id, order_num) VALUES (?, ?, ?, ?)",
            (subtopic_id, subtopic_title, topic_id, order_num)
        )
        conn.commit()
        return subtopic_id
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE subtopics SET name = ? WHERE id = ?",
            (subtopic_title, subtopic_id)
        )
        conn.commit()
        return subtopic_id


def insert_or_update_content(conn: sqlite3.Connection, subtopic_id: str, title: str, content: str) -> bool:
    """Insert or update raw content, return True if successful"""
    if not content or len(content) < 10:
        return False

    existing = conn.execute(
        "SELECT id FROM content_raw WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()

    try:
        if existing:
            conn.execute(
                "UPDATE content_raw SET markdown_content = ?, title = ?, char_count = ? WHERE subtopic_id = ?",
                (content, title, len(content), subtopic_id)
            )
        else:
            conn.execute(
                "INSERT INTO content_raw (subtopic_id, title, markdown_content, char_count) VALUES (?, ?, ?, ?)",
                (subtopic_id, title, content, len(content))
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"    Error inserting content: {e}")
        return False


def delete_existing_content(conn: sqlite3.Connection, subject_id: str):
    """Delete existing content for a subject (for clean re-ingestion)"""
    print(f"\n  Cleaning existing data for subject: {subject_id}")

    # Get topics for this subject
    topics = conn.execute(
        "SELECT id FROM topics WHERE subject_id = ?",
        (subject_id,)
    ).fetchall()

    topic_ids = [t['id'] for t in topics]

    if not topic_ids:
        print("    No existing data to clean")
        return

    # Delete content_raw entries
    for topic_id in topic_ids:
        subtopics = conn.execute(
            "SELECT id FROM subtopics WHERE topic_id = ?",
            (topic_id,)
        ).fetchall()

        for st in subtopics:
            conn.execute("DELETE FROM content_raw WHERE subtopic_id = ?", (st['id'],))
            conn.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (st['id'],))

        conn.execute("DELETE FROM subtopics WHERE topic_id = ?", (topic_id,))

    conn.execute("DELETE FROM topics WHERE subject_id = ?", (subject_id,))
    conn.commit()

    print(f"    Deleted {len(topic_ids)} topics and associated data")


def ingest_book_with_llm(
    quality_report_path: Path,
    clean_existing: bool = True,
    delay_between_chapters: float = 3.0
) -> IngestionStats:
    """
    Main ingestion function.

    Args:
        quality_report_path: Path to quality_report.json
        clean_existing: Delete existing content before ingestion
        delay_between_chapters: Seconds to wait between chapter processing

    Returns:
        IngestionStats with results
    """
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("LLM-POWERED CONTENT INGESTION PIPELINE")
    print("=" * 70)
    print(f"Quality Report: {quality_report_path.name}")

    # Parse book info
    book_info = parse_book_path(quality_report_path)
    if not book_info:
        raise ValueError(f"Could not parse book info from: {quality_report_path}")

    stats = IngestionStats(
        quality_report_path=str(quality_report_path),
        markdown_path=book_info['markdown_file'] or "NOT FOUND",
        subject_name=book_info['subject'],
        started_at=start_time.isoformat()
    )

    # Check markdown file exists
    if not book_info['markdown_file']:
        stats.issues.append("Markdown file not found")
        print(f"ERROR: Markdown file not found!")
        return stats

    markdown_path = Path(book_info['markdown_file'])
    print(f"Markdown: {markdown_path.name}")
    print(f"Subject: {book_info['subject']}")
    print(f"Syllabus: {book_info['syllabus']}")

    # Load quality report
    quality_data = load_quality_report(quality_report_path)
    if not quality_data:
        stats.issues.append("Could not load quality report")
        return stats

    chapters_data = quality_data.get('pdf_toc', {}).get('chapters', [])
    stats.total_chapters = len(chapters_data)
    print(f"Chapters in quality report: {stats.total_chapters}")

    # Load markdown
    print(f"\nLoading markdown file...")
    with open(markdown_path, 'r', encoding='utf-8') as f:
        full_markdown = f.read()
    print(f"Markdown size: {len(full_markdown):,} chars")

    # Initialize components
    conn = get_db_connection()
    chunker = MarkdownChunker(verbose=True)
    extractor = LLMContentExtractor(verbose=True)

    # Create/get subject
    subject_id = ensure_subject_exists(conn, book_info['subject'], book_info['syllabus'])

    # Clean existing data if requested
    if clean_existing:
        delete_existing_content(conn, subject_id)

    # Chunk markdown by chapters
    print(f"\n{'='*60}")
    print("STEP 1: Chunking Markdown by Chapters")
    print("="*60)

    chapter_titles_for_chunking = [
        {"chapter_number": c.get('chapter_number', i+1), "title": c.get('title', '')}
        for i, c in enumerate(chapters_data)
    ]

    chunks = chunker.chunk_by_chapters(full_markdown, chapter_titles_for_chunking)

    # Process each chapter
    print(f"\n{'='*60}")
    print("STEP 2: LLM Content Extraction")
    print("="*60)

    for chapter_data in chapters_data:
        chapter_num = chapter_data.get('chapter_number', 0)
        chapter_title = chapter_data.get('title', f'Chapter {chapter_num}')
        subtopics_data = chapter_data.get('subtopics', [])

        print(f"\n{'-'*60}")
        print(f"Chapter {chapter_num}: {chapter_title}")
        print(f"{'-'*60}")

        # Count subtopics
        stats.total_subtopics += len(subtopics_data)

        if not subtopics_data:
            print(f"  No subtopics defined, skipping")
            continue

        # Get chapter chunk
        if chapter_num not in chunks:
            print(f"  WARNING: Chapter chunk not found!")
            stats.issues.append(f"Chapter {chapter_num} not found in markdown")
            continue

        chapter_chunk = chunks[chapter_num]

        # Create topic in database
        topic_id = ensure_topic_exists(conn, subject_id, chapter_title, chapter_num)

        # Get expected subtopic titles
        expected_subtopics = [st.get('title', '') for st in subtopics_data if st.get('title')]

        # Extract using LLM
        extraction_result = extractor.extract_chapter_content(
            chapter_markdown=chapter_chunk.content,
            chapter_title=chapter_title,
            chapter_number=chapter_num,
            expected_subtopics=expected_subtopics,
            subject_name=book_info['subject']
        )

        stats.chapters_processed += 1
        stats.subtopics_found += extraction_result.total_found
        stats.subtopics_complete += extraction_result.total_complete

        # Insert extracted content into database
        for i, (subtopic_title, extracted) in enumerate(extraction_result.subtopics.items()):
            if extracted.found and extracted.content:
                # Create subtopic in database
                subtopic_id = ensure_subtopic_exists(conn, topic_id, subtopic_title, i + 1)

                # Insert content
                if insert_or_update_content(conn, subtopic_id, subtopic_title, extracted.content):
                    stats.content_inserted += 1
                    print(f"    [OK] Inserted: {subtopic_title[:50]}... ({extracted.char_count:,} chars)")
                else:
                    print(f"    [FAIL] Failed to insert: {subtopic_title[:50]}...")
            else:
                print(f"    [MISS] Not found: {subtopic_title[:50]}...")

        # Add any issues
        stats.issues.extend(extraction_result.issues)

        # Rate limiting
        if delay_between_chapters > 0:
            print(f"\n  Waiting {delay_between_chapters}s before next chapter...")
            time.sleep(delay_between_chapters)

    # Finalize
    conn.close()

    end_time = datetime.now()
    stats.finished_at = end_time.isoformat()
    stats.duration_seconds = (end_time - start_time).total_seconds()

    # Print summary
    print(f"\n{'='*70}")
    print("INGESTION COMPLETE")
    print("="*70)
    print(f"Subject: {stats.subject_name}")
    print(f"Chapters: {stats.chapters_processed}/{stats.total_chapters}")
    print(f"Subtopics Found: {stats.subtopics_found}/{stats.total_subtopics}")
    print(f"Subtopics Complete: {stats.subtopics_complete}")
    print(f"Content Inserted: {stats.content_inserted}")
    print(f"Duration: {stats.duration_seconds:.1f}s")

    if stats.issues:
        print(f"\nIssues ({len(stats.issues)}):")
        for issue in stats.issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(stats.issues) > 10:
            print(f"  ... and {len(stats.issues) - 10} more")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Powered Content Ingestion Pipeline"
    )
    parser.add_argument(
        '--quality-report', '-q',
        required=True,
        help='Path to quality_report.json file'
    )
    parser.add_argument(
        '--output-report', '-o',
        help='Path to save extraction report JSON'
    )
    parser.add_argument(
        '--keep-existing',
        action='store_true',
        help='Keep existing content instead of replacing'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=3.0,
        help='Delay between chapters in seconds (default: 3.0)'
    )

    args = parser.parse_args()

    quality_report_path = Path(args.quality_report)
    if not quality_report_path.exists():
        print(f"ERROR: Quality report not found: {quality_report_path}")
        sys.exit(1)

    # Run ingestion
    stats = ingest_book_with_llm(
        quality_report_path=quality_report_path,
        clean_existing=not args.keep_existing,
        delay_between_chapters=args.delay
    )

    # Save report if requested
    if args.output_report:
        report_path = Path(args.output_report)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(stats), f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
