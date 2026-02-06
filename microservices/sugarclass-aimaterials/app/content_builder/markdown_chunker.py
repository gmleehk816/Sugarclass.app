"""
Markdown Chunker - Smart Chapter Splitting
==========================================
Splits full markdown textbook into chapter-level chunks.
Uses quality report chapter titles as reference for boundaries.

Author: TutorRAG Pipeline v2
Date: 2026-01-04
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ChapterChunk:
    """Represents a chapter chunk extracted from markdown"""
    chapter_number: int
    title: str
    content: str
    start_line: int
    end_line: int
    char_count: int


class MarkdownChunker:
    """
    Splits full markdown into chapter-level chunks.
    Uses quality report chapter titles as boundaries.
    """

    # Common chapter header patterns in textbooks
    # Note: We look for section headers (# X.1) as the start of actual content
    CHAPTER_PATTERNS = [
        # Pattern: # 1 or # 1.
        r'^#\s+(\d+)\.?\s*$',
        # Pattern: # 1 Title or # 1. Title
        r'^#\s+(\d+)\.?\s+(.+)$',
        # Pattern: # Chapter 1 or # Chapter 1: Title
        r'^#\s+[Cc]hapter\s+(\d+)[:.]?\s*(.*)$',
        # Pattern: # CHAPTER 1
        r'^#\s+CHAPTER\s+(\d+)[:.]?\s*(.*)$',
        # Pattern: # Unit 1 or # Unit 1: Title
        r'^#\s+[Uu]nit\s+(\d+)[:.]?\s*(.*)$',
    ]

    # Section header patterns (# X.1 Subtopic) - indicates start of real content
    SECTION_PATTERNS = [
        # Pattern: # 1.1 Title
        r'^#\s+(\d+)\.(\d+)\s+(.+)$',
        # Pattern: ## 1.1 Title
        r'^##\s+(\d+)\.(\d+)\s+(.+)$',
    ]

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.compiled_patterns = [re.compile(p, re.MULTILINE) for p in self.CHAPTER_PATTERNS]
        self.section_patterns = [re.compile(p, re.MULTILINE) for p in self.SECTION_PATTERNS]

    def _log(self, message: str):
        """Print message if verbose mode enabled"""
        if self.verbose:
            try:
                print(message)
            except UnicodeEncodeError:
                # Replace problematic characters for Windows console
                safe_msg = message.encode('ascii', 'replace').decode('ascii')
                print(safe_msg)

    def find_section_headers(self, markdown: str) -> List[Tuple[int, int, str, int]]:
        """
        Find all section headers (# X.Y Title) in markdown.
        These indicate the actual start of chapter content.

        Returns:
            List of tuples: (chapter_number, section_number, line_number, char_position, header_text)
        """
        sections = []
        lines = markdown.split('\n')
        char_pos = 0

        for line_num, line in enumerate(lines):
            for pattern in self.section_patterns:
                match = pattern.match(line.strip())
                if match:
                    chapter_num = int(match.group(1))
                    section_num = int(match.group(2))
                    sections.append((chapter_num, section_num, line_num, char_pos, line.strip()))
                    break
            char_pos += len(line) + 1

        return sections

    def find_chapter_headers(self, markdown: str) -> List[Tuple[int, int, str, int]]:
        """
        Find all chapter headers in markdown.

        Returns:
            List of tuples: (chapter_number, line_number, header_text, char_position)
        """
        headers = []
        lines = markdown.split('\n')
        char_pos = 0

        for line_num, line in enumerate(lines):
            for pattern in self.compiled_patterns:
                match = pattern.match(line.strip())
                if match:
                    chapter_num = int(match.group(1))
                    headers.append((chapter_num, line_num, line.strip(), char_pos))
                    break
            char_pos += len(line) + 1  # +1 for newline

        # Sort by chapter number
        headers.sort(key=lambda x: x[0])

        return headers

    def find_chapter_by_title(
        self,
        markdown: str,
        chapter_title: str,
        chapter_number: int
    ) -> Optional[Tuple[int, int]]:
        """
        Find chapter start position by title.

        Args:
            markdown: Full markdown content
            chapter_title: Title to search for
            chapter_number: Expected chapter number

        Returns:
            Tuple of (line_number, char_position) or None if not found
        """
        lines = markdown.split('\n')
        char_pos = 0

        # Clean title for matching
        clean_title = chapter_title.lower().strip()

        for line_num, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Check if line contains the chapter title
            if clean_title in line_lower:
                # Verify it's a header line (starts with #)
                if line.strip().startswith('#'):
                    return (line_num, char_pos)
                # Or if it's just the title on its own line
                elif line_lower == clean_title:
                    return (line_num, char_pos)

            # Also check for chapter number patterns
            for pattern in self.compiled_patterns:
                match = pattern.match(line.strip())
                if match and int(match.group(1)) == chapter_number:
                    return (line_num, char_pos)

            char_pos += len(line) + 1

        return None

    def chunk_by_chapters(
        self,
        full_markdown: str,
        chapter_titles: List[Dict[str, any]]
    ) -> Dict[int, ChapterChunk]:
        """
        Split markdown into chapter chunks using quality report structure.
        Uses section headers (# X.1) to find actual content start, not TOC entries.

        Args:
            full_markdown: Full markdown content
            chapter_titles: List of dicts with 'chapter_number' and 'title' keys

        Returns:
            Dict mapping chapter_number -> ChapterChunk
        """
        self._log(f"\n{'='*60}")
        self._log("MARKDOWN CHUNKER - Splitting by Chapters")
        self._log(f"{'='*60}")
        self._log(f"Total markdown size: {len(full_markdown):,} chars")
        self._log(f"Expected chapters: {len(chapter_titles)}")

        # Find all section headers (# X.1, # X.2, etc.) - these mark actual content
        section_headers = self.find_section_headers(full_markdown)
        self._log(f"Found {len(section_headers)} section headers (# X.Y format)")

        # Build map of chapter_number -> first section line number
        # This tells us where the actual chapter content starts
        chapter_content_starts = {}
        for chapter_num, section_num, line_num, char_pos, header_text in section_headers:
            if section_num == 1:  # First section of each chapter
                if chapter_num not in chapter_content_starts:
                    chapter_content_starts[chapter_num] = (line_num, char_pos, header_text)
                    self._log(f"  Chapter {chapter_num} content starts at line {line_num}: {header_text[:50]}")

        # Process each expected chapter
        chunks = {}
        lines = full_markdown.split('\n')

        for i, chapter_info in enumerate(chapter_titles):
            chapter_num = chapter_info.get('chapter_number', i + 1)
            chapter_title = chapter_info.get('title', f'Chapter {chapter_num}')

            self._log(f"\n  Processing Chapter {chapter_num}: {chapter_title[:50]}...")

            # Find start position from section headers
            if chapter_num in chapter_content_starts:
                start_line, start_pos, header_text = chapter_content_starts[chapter_num]
                self._log(f"    Found via section header at line {start_line}")
            else:
                # Fallback: search by title in the content (not TOC)
                # Look for title after line 400 (skip TOC area)
                result = self._find_content_start(full_markdown, chapter_title, chapter_num, min_line=400)
                if result:
                    start_line, start_pos = result
                    self._log(f"    Found via title search at line {start_line}")
                else:
                    self._log(f"    WARNING: Chapter content not found!")
                    continue

            # Find end position (start of next chapter content)
            end_line = len(lines)
            next_chapter_num = chapter_num + 1

            if next_chapter_num in chapter_content_starts:
                end_line = chapter_content_starts[next_chapter_num][0]
            else:
                # Look for next chapter in section headers
                for ch_num, sec_num, ln, _, _ in section_headers:
                    if ch_num == next_chapter_num and sec_num == 1:
                        end_line = ln
                        break

            # Extract chapter content
            chapter_content = '\n'.join(lines[start_line:end_line])

            chunks[chapter_num] = ChapterChunk(
                chapter_number=chapter_num,
                title=chapter_title,
                content=chapter_content,
                start_line=start_line,
                end_line=end_line,
                char_count=len(chapter_content)
            )

            self._log(f"    Extracted: lines {start_line}-{end_line} ({len(chapter_content):,} chars)")

        # Summary
        self._log(f"\n{'='*60}")
        self._log(f"CHUNKING COMPLETE")
        self._log(f"{'='*60}")
        self._log(f"Expected: {len(chapter_titles)} chapters")
        self._log(f"Extracted: {len(chunks)} chapters")

        if len(chunks) < len(chapter_titles):
            missing = set(c['chapter_number'] for c in chapter_titles) - set(chunks.keys())
            self._log(f"Missing chapters: {missing}")

        return chunks

    def _find_content_start(
        self,
        markdown: str,
        chapter_title: str,
        chapter_number: int,
        min_line: int = 0
    ) -> Optional[Tuple[int, int]]:
        """
        Find chapter content start position, skipping TOC area.

        Args:
            markdown: Full markdown content
            chapter_title: Title to search for
            chapter_number: Expected chapter number
            min_line: Minimum line number to consider (skip TOC)

        Returns:
            Tuple of (line_number, char_position) or None if not found
        """
        lines = markdown.split('\n')
        char_pos = 0

        # Calculate char_pos for min_line
        for i in range(min(min_line, len(lines))):
            char_pos += len(lines[i]) + 1

        clean_title = chapter_title.lower().strip()

        for line_num in range(min_line, len(lines)):
            line = lines[line_num]
            line_lower = line.lower().strip()

            # Check if line contains the chapter title as a header
            if clean_title in line_lower and line.strip().startswith('#'):
                return (line_num, char_pos)

            char_pos += len(line) + 1

        return None

    def chunk_large_chapter(
        self,
        chapter_content: str,
        max_chunk_size: int = 80000
    ) -> List[str]:
        """
        Split a large chapter into smaller chunks for LLM processing.

        Args:
            chapter_content: Chapter markdown content
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of content chunks
        """
        if len(chapter_content) <= max_chunk_size:
            return [chapter_content]

        chunks = []
        lines = chapter_content.split('\n')
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1

            # If adding this line would exceed limit, save current chunk
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size

        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks


def test_chunker():
    """Test the markdown chunker with a sample file"""
    print("Testing MarkdownChunker...")

    # Test with Physics markdown
    physics_md_path = Path(r"C:\Users\gmhome\SynologyDrive\coding\pdftomarkdown\output\materials_output\cie igcse\Physics (0625)\Textbook\Cambridge IGCSE Physics Coursebook 9781108888073.md")

    if not physics_md_path.exists():
        print(f"Test file not found: {physics_md_path}")
        return

    # Load markdown
    with open(physics_md_path, 'r', encoding='utf-8') as f:
        markdown = f.read()

    # Sample chapter titles from quality report
    sample_chapters = [
        {"chapter_number": 1, "title": "Making measurements"},
        {"chapter_number": 2, "title": "Describing motion"},
        {"chapter_number": 3, "title": "Forces and motion"},
        {"chapter_number": 4, "title": "Turning effects"},
        {"chapter_number": 5, "title": "Forces and matter"},
    ]

    chunker = MarkdownChunker(verbose=True)
    chunks = chunker.chunk_by_chapters(markdown, sample_chapters)

    print(f"\n\nExtracted {len(chunks)} chunks:")
    for ch_num, chunk in chunks.items():
        print(f"  Chapter {ch_num}: {chunk.char_count:,} chars - {chunk.title[:40]}...")


if __name__ == "__main__":
    test_chunker()
