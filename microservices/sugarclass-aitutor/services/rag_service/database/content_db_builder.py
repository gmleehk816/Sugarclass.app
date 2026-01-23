"""
Content Database Builder

Scans the tutorrag/database folder structure and populates
the content database with syllabus hierarchy and content.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)


@dataclass
class ContentRecord:
    """Represents a content item from the folder structure."""
    syllabus: str
    subject: str
    chapter: str
    subtopic: str
    content_type: str
    file_path: str
    markdown_content: str
    content_hash: str
    word_count: int
    difficulty_level: str
    metadata: Dict[str, Any]


class ContentDatabaseBuilder:
    """
    Scans the tutorrag/database folder structure and populates
    the content database with syllabus hierarchy and content.

    Expected folder structure:
    content_root/
    ├── {syllabus}/           # e.g., 'CIE_IGCSE', 'IB', 'AQA'
    │   ├── {subject}/        # e.g., 'Mathematics', 'Physics'
    │   │   ├── {chapter}/    # e.g., 'Differentiation'
    │   │   │   ├── {subtopic}/  # e.g., 'Chain_Rule'
    │   │   │   │   ├── textbook.md
    │   │   │   │   ├── exercises.md
    │   │   │   │   └── exam_qanda.md
    """

    def __init__(
        self,
        content_root: str,
        database_url: str,
        embedding_model: Any = None
    ):
        self.content_root = Path(content_root)
        self.database_url = database_url
        self.embedding_model = embedding_model
        self.pool: Optional[asyncpg.Pool] = None

        # Content type mapping based on filename patterns
        self.content_type_patterns = {
            'textbook': ['textbook.md', 'content.md', 'theory.md', 'notes.md', 'lesson.md'],
            'exercise': ['exercises.md', 'practice.md', 'problems.md', 'worksheet.md', 'questions.md'],
            'exam_qa': ['exam_qanda.md', 'exam.md', 'past_papers.md', 'exam_questions.md', 'marking_scheme.md']
        }

        # Difficulty keywords for inference
        self.difficulty_keywords = {
            'extended': ['extended', 'advanced', 'higher', 'hl', 'hard'],
            'foundation': ['foundation', 'basic', 'lower', 'sl', 'easy', 'intro'],
            'core': ['core', 'standard', 'medium', 'regular']
        }

    async def connect(self) -> None:
        """Establish database connection pool."""
        if asyncpg is None:
            raise ImportError("asyncpg is required. Install with: pip install asyncpg")

        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info(f"Connected to database: {self.database_url.split('@')[-1]}")

    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")

    async def build_database(self, force_rebuild: bool = False) -> Dict[str, int]:
        """
        Main entry point: scan folder structure and populate database.

        Args:
            force_rebuild: If True, update all records even if unchanged

        Returns:
            Statistics about the build process
        """
        stats = {
            'total_files': 0,
            'new_records': 0,
            'updated_records': 0,
            'skipped_records': 0,
            'errors': 0,
            'syllabi_found': 0,
            'subjects_found': 0
        }

        if not self.content_root.exists():
            raise FileNotFoundError(f"Content root not found: {self.content_root}")

        logger.info(f"Scanning content from: {self.content_root}")
        print(f"Scanning content from: {self.content_root}")

        # Walk through the folder structure
        syllabi = [d for d in self.content_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
        stats['syllabi_found'] = len(syllabi)

        for syllabus_dir in syllabi:
            syllabus_name = self._normalize_name(syllabus_dir.name)
            print(f"  Processing syllabus: {syllabus_name}")

            subjects = [d for d in syllabus_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

            for subject_dir in subjects:
                subject_name = self._normalize_name(subject_dir.name)
                stats['subjects_found'] += 1

                # Check if subject directory contains chapters or direct content
                await self._process_subject(
                    syllabus_name,
                    subject_name,
                    subject_dir,
                    stats,
                    force_rebuild
                )

        print(f"\nBuild complete:")
        print(f"   - Total files scanned: {stats['total_files']}")
        print(f"   - New records: {stats['new_records']}")
        print(f"   - Updated records: {stats['updated_records']}")
        print(f"   - Skipped (unchanged): {stats['skipped_records']}")
        print(f"   - Errors: {stats['errors']}")

        return stats

    async def _process_subject(
        self,
        syllabus: str,
        subject: str,
        subject_path: Path,
        stats: Dict[str, int],
        force_rebuild: bool
    ) -> None:
        """Process a subject directory."""

        # Get all subdirectories (chapters)
        chapters = [d for d in subject_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        if chapters:
            for chapter_dir in chapters:
                chapter_name = self._normalize_name(chapter_dir.name)
                await self._process_chapter(
                    syllabus, subject, chapter_name,
                    chapter_dir, stats, force_rebuild
                )

        # Also check for direct markdown files in subject directory
        md_files = list(subject_path.glob('*.md'))
        if md_files:
            await self._process_subtopic(
                syllabus, subject, subject,  # Use subject as chapter
                subject,  # Use subject as subtopic
                subject_path, stats, force_rebuild
            )

    async def _process_chapter(
        self,
        syllabus: str,
        subject: str,
        chapter: str,
        chapter_path: Path,
        stats: Dict[str, int],
        force_rebuild: bool
    ) -> None:
        """Process a chapter directory, handling both subtopics and direct files."""

        # Check for subtopic directories
        subtopics = [d for d in chapter_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        if subtopics:
            for subtopic_dir in subtopics:
                subtopic_name = self._normalize_name(subtopic_dir.name)
                await self._process_subtopic(
                    syllabus, subject, chapter,
                    subtopic_name, subtopic_dir, stats, force_rebuild
                )

        # Also process direct markdown files in chapter directory
        md_files = list(chapter_path.glob('*.md'))
        if md_files:
            await self._process_subtopic(
                syllabus, subject, chapter,
                chapter,  # Use chapter name as subtopic
                chapter_path, stats, force_rebuild
            )

    async def _process_subtopic(
        self,
        syllabus: str,
        subject: str,
        chapter: str,
        subtopic: str,
        subtopic_path: Path,
        stats: Dict[str, int],
        force_rebuild: bool
    ) -> None:
        """Process markdown files in a subtopic directory."""

        for file_path in subtopic_path.glob('*.md'):
            stats['total_files'] += 1

            try:
                # Determine content type
                content_type = self._determine_content_type(file_path.name)

                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                        content = f.read()

                if not content.strip():
                    logger.warning(f"Empty file: {file_path}")
                    continue

                # Calculate hash for change detection
                content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

                # Create record
                record = ContentRecord(
                    syllabus=syllabus,
                    subject=subject,
                    chapter=chapter,
                    subtopic=subtopic,
                    content_type=content_type,
                    file_path=str(file_path),
                    markdown_content=content,
                    content_hash=content_hash,
                    word_count=len(content.split()),
                    difficulty_level=self._infer_difficulty(file_path, content),
                    metadata={
                        'filename': file_path.name,
                        'file_size': file_path.stat().st_size,
                        'last_modified': datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    }
                )

                # Upsert to database
                result = await self._upsert_record(record, force_rebuild)

                if result == 'new':
                    stats['new_records'] += 1
                elif result == 'updated':
                    stats['updated_records'] += 1
                else:
                    stats['skipped_records'] += 1

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                print(f"    Error processing {file_path.name}: {e}")
                stats['errors'] += 1

    def _normalize_name(self, name: str) -> str:
        """Normalize folder/file names for display."""
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Remove common prefixes like numbers
        if len(name) > 0 and name[0].isdigit() and '.' in name[:4]:
            name = name.split('.', 1)[-1].strip()
        return name.strip()

    def _determine_content_type(self, filename: str) -> str:
        """Determine content type based on filename."""
        filename_lower = filename.lower()

        for content_type, patterns in self.content_type_patterns.items():
            if any(pattern in filename_lower for pattern in patterns):
                return content_type

        # Default based on common patterns
        if 'exam' in filename_lower or 'test' in filename_lower:
            return 'exam_qa'
        elif 'exercise' in filename_lower or 'practice' in filename_lower:
            return 'exercise'

        return 'textbook'  # Default

    def _infer_difficulty(self, file_path: Path, content: str) -> str:
        """Infer difficulty level from path or content."""
        path_str = str(file_path).lower()
        content_lower = content[:500].lower()  # Check first 500 chars

        for difficulty, keywords in self.difficulty_keywords.items():
            if any(kw in path_str or kw in content_lower for kw in keywords):
                return difficulty

        return 'core'  # Default

    async def _upsert_record(self, record: ContentRecord, force_rebuild: bool = False) -> str:
        """
        Insert or update a content record.

        Returns:
            'new', 'updated', or 'skipped'
        """
        async with self.pool.acquire() as conn:
            # Check if record exists
            existing = await conn.fetchrow(
                """
                SELECT id, content_hash FROM syllabus_hierarchy
                WHERE file_path = $1
                """,
                record.file_path
            )

            if existing:
                if not force_rebuild and existing['content_hash'] == record.content_hash:
                    return 'skipped'  # No changes

                # Update existing record
                await conn.execute(
                    """
                    UPDATE syllabus_hierarchy SET
                        syllabus = $1,
                        subject = $2,
                        chapter = $3,
                        subtopic = $4,
                        content_type = $5,
                        markdown_content = $6,
                        content_hash = $7,
                        word_count = $8,
                        difficulty_level = $9,
                        metadata = $10,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $11
                    """,
                    record.syllabus,
                    record.subject,
                    record.chapter,
                    record.subtopic,
                    record.content_type,
                    record.markdown_content,
                    record.content_hash,
                    record.word_count,
                    record.difficulty_level,
                    json.dumps(record.metadata),
                    existing['id']
                )
                return 'updated'
            else:
                # Insert new record
                await conn.execute(
                    """
                    INSERT INTO syllabus_hierarchy (
                        syllabus, subject, chapter, subtopic, content_type,
                        file_path, markdown_content, content_hash, word_count,
                        difficulty_level, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (file_path) DO UPDATE SET
                        markdown_content = EXCLUDED.markdown_content,
                        content_hash = EXCLUDED.content_hash,
                        word_count = EXCLUDED.word_count,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    record.syllabus,
                    record.subject,
                    record.chapter,
                    record.subtopic,
                    record.content_type,
                    record.file_path,
                    record.markdown_content,
                    record.content_hash,
                    record.word_count,
                    record.difficulty_level,
                    json.dumps(record.metadata)
                )
                return 'new'

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the content database."""
        async with self.pool.acquire() as conn:
            stats = {}

            # Total records
            stats['total_records'] = await conn.fetchval(
                "SELECT COUNT(*) FROM syllabus_hierarchy"
            )

            # By syllabus
            rows = await conn.fetch(
                """
                SELECT syllabus, COUNT(*) as count
                FROM syllabus_hierarchy
                GROUP BY syllabus
                ORDER BY count DESC
                """
            )
            stats['by_syllabus'] = {row['syllabus']: row['count'] for row in rows}

            # By content type
            rows = await conn.fetch(
                """
                SELECT content_type, COUNT(*) as count
                FROM syllabus_hierarchy
                GROUP BY content_type
                """
            )
            stats['by_content_type'] = {row['content_type']: row['count'] for row in rows}

            # Total word count
            stats['total_words'] = await conn.fetchval(
                "SELECT SUM(word_count) FROM syllabus_hierarchy"
            ) or 0

            return stats

    async def search_content(
        self,
        query: str,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search content using full-text search."""
        async with self.pool.acquire() as conn:
            conditions = ["to_tsvector('english', markdown_content) @@ plainto_tsquery('english', $1)"]
            params = [query]
            param_idx = 2

            if syllabus:
                conditions.append(f"syllabus = ${param_idx}")
                params.append(syllabus)
                param_idx += 1

            if subject:
                conditions.append(f"subject = ${param_idx}")
                params.append(subject)
                param_idx += 1

            if content_type:
                conditions.append(f"content_type = ${param_idx}")
                params.append(content_type)
                param_idx += 1

            where_clause = " AND ".join(conditions)

            rows = await conn.fetch(
                f"""
                SELECT id, syllabus, subject, chapter, subtopic, content_type,
                       difficulty_level, word_count, file_path
                FROM syllabus_hierarchy
                WHERE {where_clause}
                LIMIT {limit}
                """,
                *params
            )

            return [dict(row) for row in rows]
