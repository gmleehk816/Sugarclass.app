"""
Automated Textbook Processing Pipeline
======================================
Complete automation: Markdown → LLM Structure → Ingestion → Rewriting

Usage:
    # Process a single markdown file
    python auto_process_textbook.py <markdown_file> [--subject-name "Name"] [--syllabus "CIE IGCSE"]
    
    # Auto-discover and process all unprocessed markdown files
    python auto_process_textbook.py --auto-discover --source-dir "path/to/markdown/files"
    
    # Only rewrite existing content (skip structure+ingest)
    python auto_process_textbook.py --rewrite-only --subject-id <subject_id>

This script:
1. Sends markdown to Gemini API to generate chapter/subtopic structure
2. Ingests raw content into database using title-based extraction
3. (Optional) Runs rewriting pipeline to convert markdown → educational HTML
"""
import sys
import json
import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher
import argparse

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.api_config import make_api_call

# Configuration
DB_PATH = Path(__file__).parent.parent / 'database' / 'rag_content.db'
# Default to /books if in Docker, otherwise use a relative path to archive
DEFAULT_SOURCE_DIR = Path("/books") if Path("/books").exists() else Path(__file__).parent.parent / 'archive'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def sanitize_id(name: str) -> str:
    """Create a safe ID from a name"""
    clean = re.sub(r'[^\w\s-]', '', name)
    clean = re.sub(r'[-\s]+', '_', clean)
    return clean.lower().strip('_')[:50]


def fuzzy_match(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


# ============================================================
# AUTO-DISCOVERY: Find unprocessed markdown books
# ============================================================

def get_existing_subjects():
    """Get all subject IDs currently in the database."""
    conn = get_conn()
    subjects = {row['id'] for row in conn.execute("SELECT id FROM subjects").fetchall()}
    conn.close()
    return subjects


def get_unprocessed_rewrites():
    """Get subjects that have raw content but incomplete rewrites."""
    conn = get_conn()
    results = conn.execute("""
        SELECT t.subject_id, 
               COUNT(DISTINCT cr.subtopic_id) as raw_count,
               COUNT(DISTINCT cp.subtopic_id) as processed_count
        FROM topics t
        LEFT JOIN subtopics s ON s.topic_id = t.id
        LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
        LEFT JOIN content_processed cp ON cp.subtopic_id = s.id
        GROUP BY t.subject_id
        HAVING raw_count > processed_count
    """).fetchall()
    conn.close()
    return [(r['subject_id'], r['raw_count'], r['processed_count']) for r in results]


def discover_markdown_files(source_dir: Path):
    """Discover all markdown files in the source directory structure."""
    markdown_files = []
    
    # Search for .md files in Textbook folders
    for md_path in source_dir.rglob("*.md"):
        # Skip quality reports
        if "_quality_report" in md_path.name:
            continue
        # Skip very small files (likely not full textbooks)
        if md_path.stat().st_size < 10000:
            continue
        # Skip chunk files (partial textbooks)
        if "chunk_" in md_path.name or "_chunks" in str(md_path):
            continue
        # Skip page-range files (like _p0-20.md)
        if re.search(r'_p\d+-\d+\.md$', md_path.name):
            continue
        # Skip vlm subdirectory files (usually duplicates)
        if "\\vlm\\" in str(md_path) or "/vlm/" in str(md_path):
            continue
        
        # Determine subject info from path
        # Expected structure: materials_output/[Board]/[Subject]/Textbook/Name.md
        parts = md_path.parts
        
        # Try to extract board/syllabus and subject from path
        syllabus = "Unknown"
        subject_name = md_path.stem
        
        try:
            # Find index of "materials_output" in path
            if "materials_output" in parts:
                idx = parts.index("materials_output")
                if idx + 2 < len(parts):
                    syllabus = parts[idx + 1]  # CIE IGCSE, IB, etc.
                    subject_name = parts[idx + 2].split('(')[0].strip()  # Subject folder name
        except:
            pass
        
        markdown_files.append({
            'path': md_path,
            'subject_name': subject_name,
            'syllabus': syllabus,
            'subject_id': sanitize_id(f"{subject_name}_{md_path.stem}")[:50]
        })
    
    return markdown_files


def auto_discover_and_process(source_dir: Path, skip_existing: bool = True, rewrite_incomplete: bool = True):
    """Auto-discover and process unprocessed markdown files."""
    print("="*60)
    print("AUTO-DISCOVERY MODE")
    print("="*60)
    print(f"Source directory: {source_dir}")
    
    # Get existing subjects
    existing_subjects = get_existing_subjects()
    print(f"Existing subjects in DB: {len(existing_subjects)}")
    
    # Discover markdown files
    all_files = discover_markdown_files(source_dir)
    print(f"Discovered markdown files: {len(all_files)}")
    
    # Filter to unprocessed files
    if skip_existing:
        new_files = [f for f in all_files if f['subject_id'] not in existing_subjects]
        print(f"New (unprocessed) files: {len(new_files)}")
    else:
        new_files = all_files
    
    # Print discovered files
    print("\n--- Unprocessed Markdown Files ---")
    for i, f in enumerate(new_files[:20], 1):  # Show first 20
        print(f"  {i}. {f['subject_name']} ({f['syllabus']})")
        print(f"     Path: {f['path'].name}")
        print(f"     ID: {f['subject_id']}")
    if len(new_files) > 20:
        print(f"  ... and {len(new_files) - 20} more")
    
    # Check for incomplete rewrites
    incomplete_rewrites = get_unprocessed_rewrites()
    if incomplete_rewrites:
        print(f"\n--- Subjects with Incomplete Rewrites: {len(incomplete_rewrites)} ---")
        for subj_id, raw, processed in incomplete_rewrites:
            print(f"  - {subj_id}: {processed}/{raw} rewritten ({100*processed/raw:.0f}%)")
    
    if not new_files and not incomplete_rewrites:
        print("\n✅ All markdown files are processed and rewritten!")
        return
    
    # Ask for confirmation
    print("\n" + "-"*60)
    total_tasks = len(new_files) + len(incomplete_rewrites)
    print(f"Ready to process {total_tasks} tasks:")
    print(f"  - {len(new_files)} new markdown files to ingest")
    print(f"  - {len(incomplete_rewrites)} subjects need more rewrites")
    
    # Process new files
    processed_count = 0
    for f in new_files:
        print(f"\n{'='*60}")
        print(f"Processing: {f['subject_name']}")
        print(f"{'='*60}")
        
        try:
            # Generate quality report
            quality_report = generate_quality_report(f['path'])
            
            # Ingest content
            result = ingest_content(
                quality_report,
                f['path'],
                subject_name=f['subject_name'],
                syllabus=f['syllabus']
            )
            
            # Rewrite content
            rewrite_content(result['subject_id'])
            
            processed_count += 1
            print(f"\n✅ Completed: {f['subject_name']}")
            
        except Exception as e:
            print(f"\n❌ Error processing {f['subject_name']}: {e}")
            continue
    
    # Process incomplete rewrites
    if rewrite_incomplete:
        for subj_id, raw, processed in incomplete_rewrites:
            print(f"\n{'='*60}")
            print(f"Completing rewrites for: {subj_id}")
            print(f"{'='*60}")
            
            try:
                rewrite_content(subj_id)
                print(f"✅ Rewrites completed for {subj_id}")
            except Exception as e:
                print(f"❌ Error rewriting {subj_id}: {e}")
    
    print("\n" + "="*60)
    print("AUTO-DISCOVERY COMPLETE")
    print("="*60)
    print(f"Processed: {processed_count} new files")
    print(f"Rewrites completed for: {len(incomplete_rewrites)} subjects")


# ============================================================
# STEP 1: Generate Quality Report with LLM
# ============================================================

def generate_quality_report(markdown_path: Path) -> dict:
    """Send markdown to Gemini and get structured quality report back."""
    print("\n" + "="*60)
    print("STEP 1: Generating Structure with LLM")
    print("="*60)
    
    # Strategy A: Check for high-fidelity .structure.json (Preferred)
    structure_json_path = markdown_path.parent / f"{markdown_path.stem.split('__')[0]}.structure.json"
    if not structure_json_path.exists():
        # Try without any suffixes
        structure_json_path = markdown_path.parent / f"{markdown_path.stem}.structure.json"
    
    if structure_json_path.exists():
        print(f"Found high-fidelity structure: {structure_json_path.name}")
        with open(structure_json_path, 'r', encoding='utf-8') as f:
            raw_struct = json.load(f)
        
        # Convert to internal quality_report format
        quality_report = {
            "source_file": str(markdown_path.name),
            "subject": raw_struct.get("title", "Unknown"),
            "chapters": [],
            "total_chapters": raw_struct.get("total_chapters", 0),
            "total_subtopics": raw_struct.get("total_subtopics", 0),
            "is_high_fidelity": True
        }
        
        for ch in raw_struct.get("chapters", []):
            chapter = {
                "number": ch.get("chapter"),
                "title": ch.get("title"),
                "line_number": ch.get("line_number"),
                "subtopics": []
            }
            for st in ch.get("subtopics", []):
                chapter["subtopics"].append({
                    "number": st.get("subtopic"),
                    "title": st.get("title"),
                    "line_number": st.get("line_number")
                })
            quality_report["chapters"].append(chapter)
            
        print(f"✅ Using high-fidelity structure: {len(quality_report['chapters'])} chapters")
        return quality_report

    # Strategy B: Check if quality report already exists
    report_path = markdown_path.parent / f"{markdown_path.stem}_quality_report.json"
    if report_path.exists():
        print(f"Found existing quality report: {report_path.name}")
        with open(report_path, 'r', encoding='utf-8') as f:
            quality_report = json.load(f)
        
        # Validate it has chapters
        if quality_report.get('chapters') and len(quality_report['chapters']) > 0:
            total_subtopics = sum(len(ch.get('subtopics', [])) for ch in quality_report['chapters'])
            print(f"✅ Using existing report: {len(quality_report['chapters'])} chapters, {total_subtopics} subtopics")
            return quality_report
        else:
            print("Existing report is invalid, regenerating...")
    
    content = markdown_path.read_text(encoding='utf-8', errors='ignore')
    print(f"Loaded markdown: {len(content):,} characters")
    
    # Truncate if too large for API
    max_chars = 100000
    if len(content) > max_chars:
        content = content[:60000] + "\n\n[...content truncated...]\n\n" + content[-40000:]
        print(f"Truncated to {len(content):,} characters for API")
    
    prompt = f"""Analyze this educational textbook markdown and extract its structure.

Return ONLY a valid JSON object with this exact structure:
{{
    "subject": "Subject Name",
    "chapters": [
        {{
            "number": 1,
            "title": "Chapter Title",
            "subtopics": [
                {{
                    "number": "1.1",
                    "title": "Subtopic Title"
                }}
            ]
        }}
    ]
}}

Rules:
1. Extract ALL chapters and subtopics from the table of contents or headings
2. Use the exact titles as they appear in the document
3. Number chapters sequentially (1, 2, 3...)
4. Number subtopics as chapter.section (1.1, 1.2, 2.1, etc.)
5. Return ONLY the JSON, no markdown formatting, no explanation

MARKDOWN CONTENT:
{content}"""

    messages = [
        {"role": "system", "content": "You are a document structure analyzer. Return only valid JSON."},
        {"role": "user", "content": prompt}
    ]
    
    print("Calling Gemini API to analyze structure...")
    result = make_api_call(messages, max_tokens=16000, temperature=0.1, auto_fallback=True)
    
    if not result['success']:
        raise Exception(f"API Error: {result.get('error')}")
    
    response_text = result['content'].strip()
    
    # Clean up response if wrapped in markdown
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    
    structure = json.loads(response_text)
    
    quality_report = {
        "source_file": str(markdown_path.name),
        "subject": structure.get("subject", "Unknown"),
        "chapters": structure.get("chapters", []),
        "total_chapters": len(structure.get("chapters", [])),
        "total_subtopics": sum(len(ch.get("subtopics", [])) for ch in structure.get("chapters", []))
    }
    
    # Save quality report
    report_path = markdown_path.parent / f"{markdown_path.stem}_quality_report.json"
    report_path.write_text(json.dumps(quality_report, indent=2), encoding='utf-8')
    
    print(f"✅ Generated quality report: {quality_report['total_chapters']} chapters, {quality_report['total_subtopics']} subtopics")
    print(f"   Saved to: {report_path.name}")
    
    return quality_report


# ============================================================
# STEP 2: Extract Content by Title with Fuzzy Matching
# ============================================================

def extract_content_by_line_numbers(lines: list, start_line: int, end_line: int) -> str:
    """Extract content between two line numbers (1-indexed)."""
    # Convert to 0-indexed and slice
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line - 1)
    
    if start_idx >= end_idx:
        return ""
        
    return "\n".join(lines[start_idx:end_idx]).strip()


def find_chapter_boundary(md_content: str, title: str, start_from: int = 0) -> int:
    """Find the position of a chapter title (as a markdown header) for boundary detection."""
    content_lower = md_content.lower()
    title_lower = title.lower().strip()
    
    # Look for markdown headers: "# TITLE" or "# title"
    header_patterns = [
        f"\n# {title_lower}",
        f"\n# {title_lower.upper()}",
        f"\n## {title_lower}",
        f"\n## {title_lower.upper()}",
    ]
    
    for pattern in header_patterns:
        pos = content_lower.find(pattern, start_from)
        if pos != -1:
            return pos
    
    # Also try bold headers like "**TITLE**" on its own line
    bold_patterns = [
        f"\n**{title_lower}**",
        f"\n**{title_lower.upper()}**",
    ]
    for pattern in bold_patterns:
        pos = content_lower.find(pattern, start_from)
        if pos != -1:
            return pos
    
    return -1


def extract_content_by_title(md_content: str, title: str, next_title: str = None, section_num: str = None, is_chapter: bool = False) -> tuple:
    """Extract content from markdown using title-based search with fuzzy matching."""
    content_lower = md_content.lower()
    title_lower = title.lower().strip()
    
    # For chapters (no section number), we need a smarter TOC skip threshold
    # Find where the TOC ends by looking for the first major content header
    if is_chapter:
        # Look for the first actual content header after the table of contents
        # Usually appears after "CONTENTS" section
        contents_pos = content_lower.find('contents')
        if contents_pos != -1:
            # Find the next header after the contents section (usually the first chapter)
            first_header_match = content_lower.find('\n# ', contents_pos + 100)
            toc_skip = max(first_header_match - 100, 0) if first_header_match != -1 else 1000
        else:
            toc_skip = 1000
    else:
        toc_skip = 5000  # Default for subtopics with section numbers
    
    # Helper to find end boundary
    def find_end_pos(start: int) -> int:
        if next_title:
            # Use chapter boundary detection for chapters (finds # headers)
            boundary = find_chapter_boundary(md_content, next_title, start + 100)
            if boundary != -1:
                return boundary
        # Default: 15000 chars
        return start + 15000
    
    # Strategy 1: Search for section number + title
    if section_num:
        # Create alternative section number formats (1.1 -> 1-1, 1·1, etc.)
        section_variants = [
            section_num,
            section_num.replace('.', '-'),
            section_num.replace('.', '·'),
            section_num.replace('.', ' '),
        ]
        
        patterns = []
        for sec in section_variants:
            patterns.extend([
                f"# {sec} {title_lower}",
                f"# {sec}",
                f"#{sec} ",
                f"\n{sec} {title_lower}",
                f"\n{sec} ",
            ])
        
        for pattern in patterns:
            pos = content_lower.find(pattern)
            if pos != -1 and pos > toc_skip:
                start_pos = pos
                end_pos = find_end_pos(start_pos)
                return md_content[start_pos:end_pos].strip(), None
    
    # Strategy 2: Look for markdown header with title
    header_pattern = f"# {title_lower}"
    pos = content_lower.find(header_pattern, toc_skip)
    if pos != -1:
        start_pos = pos
        end_pos = find_end_pos(start_pos)
        return md_content[start_pos:end_pos].strip(), None
    
    # Strategy 3: Exact match - find SECOND occurrence (skip TOC)
    first_pos = content_lower.find(title_lower)
    if first_pos != -1:
        second_pos = content_lower.find(title_lower, first_pos + len(title_lower))
        if second_pos != -1 and second_pos > toc_skip:
            start_pos = second_pos
            end_pos = find_end_pos(start_pos)
            return md_content[start_pos:end_pos].strip(), None
        elif first_pos > toc_skip * 2:
            start_pos = first_pos
            end_pos = find_end_pos(start_pos)
            return md_content[start_pos:end_pos].strip(), None
    
    # Strategy 4: Fuzzy matching
    best_match = None
    best_ratio = 0.0
    best_pos = -1
    
    # Create section number variants for matching
    section_variants = []
    if section_num:
        section_variants = [
            section_num,
            section_num.replace('.', '-'),
            section_num.replace('.', '·'),
            section_num.replace('.', ' '),
        ]
    
    lines = md_content.split('\n')
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if len(line_stripped) < 5 or len(line_stripped) > 150:
            continue
        
        # Check if line contains any section variant
        has_section = section_num and any(sv in line_stripped for sv in section_variants)
        
        if has_section:
            title_no_num = title.lower()
            line_no_num = re.sub(r'^#*\s*\d+[-·.\s]\d+\s*', '', line_stripped.lower())
            ratio = fuzzy_match(title_no_num, line_no_num)
            
            if ratio > best_ratio and ratio > 0.5:
                best_ratio = ratio
                best_match = line_stripped
                best_pos = sum(len(l) + 1 for l in lines[:i])
        else:
            ratio = fuzzy_match(title, line_stripped)
            if ratio > best_ratio and ratio > 0.7:
                line_pos = sum(len(l) + 1 for l in lines[:i])
                if line_pos > toc_skip:
                    best_ratio = ratio
                    best_match = line_stripped
                    best_pos = line_pos
    
    if best_match and best_pos > toc_skip:
        end_pos = find_end_pos(best_pos)
        return md_content[best_pos:end_pos].strip(), best_match
    
    return "", None


# ============================================================
# STEP 3: Ingest Content into Database
# ============================================================

def ingest_content(quality_report: dict, markdown_path: Path, subject_name: str = None, syllabus: str = "CIE IGCSE"):
    """Ingest content from markdown into database using quality report structure."""
    print("\n" + "="*60)
    print("STEP 2: Ingesting Content into Database")
    print("="*60)
    
    md_content = markdown_path.read_text(encoding='utf-8', errors='ignore')
    md_lines = md_content.splitlines()
    
    conn = get_conn()
    
    # Use provided subject name or from quality report
    subject_name = subject_name or quality_report.get('subject', 'Unknown Subject')
    subject_id = sanitize_id(subject_name)
    syllabus_id = sanitize_id(syllabus)
    
    # Check if subject exists
    existing = conn.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    if existing:
        print(f"Subject '{subject_name}' already exists, updating...")
        # Delete existing raw content and structure, but KEEP processed content
        conn.execute("DELETE FROM content_raw WHERE subtopic_id IN (SELECT id FROM subtopics WHERE topic_id IN (SELECT id FROM topics WHERE subject_id = ?))", (subject_id,))
        # Keep content_processed - don't delete rewrites!
        conn.execute("DELETE FROM subtopics WHERE topic_id IN (SELECT id FROM topics WHERE subject_id = ?)", (subject_id,))
        conn.execute("DELETE FROM topics WHERE subject_id = ?", (subject_id,))
        conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
    
    # Create subject
    conn.execute(
        "INSERT INTO subjects (id, name, syllabus_id, code) VALUES (?, ?, ?, ?)",
        (subject_id, subject_name, syllabus_id, syllabus.split()[0] if ' ' in syllabus else syllabus)
    )
    conn.commit()
    print(f"Created subject: {subject_name}")
    
    # Build list of all subtopic titles for next-title lookup
    # Include chapters with no subtopics as their own entry
    all_subtopics = []
    all_chapter_titles = []
    for ch in quality_report['chapters']:
        all_chapter_titles.append(ch['title'])
        if ch.get('subtopics'):
            for st in ch['subtopics']:
                all_subtopics.append(st['title'])
        else:
            # Chapter with no subtopics - treat chapter itself as a subtopic
            all_subtopics.append(ch['title'])
    
    # Process chapters
    topic_count = 0
    subtopic_count = 0
    content_count = 0
    
    for ch_idx, ch in enumerate(quality_report['chapters']):
        ch_num = ch['number']
        ch_title = ch['title']
        
        # Create topic
        topic_id = f"{subject_id}_ch{ch_num}"
        conn.execute(
            "INSERT INTO topics (id, name, subject_id, type, order_num) VALUES (?, ?, ?, ?, ?)",
            (topic_id, ch_title, subject_id, 'Chapter', ch_num)
        )
        topic_count += 1
        print(f"\n  Chapter {ch_num}: {ch_title}")
        
        # Handle chapters without subtopics - treat the chapter as a single subtopic
        if not ch.get('subtopics'):
            # Create subtopic using chapter title
            subtopic_id = f"{topic_id}_{sanitize_id(ch_title)}"
            conn.execute(
                "INSERT INTO subtopics (id, name, topic_id, order_num) VALUES (?, ?, ?, ?)",
                (subtopic_id, ch_title, topic_id, 1)
            )
            subtopic_count += 1
            
            # Get next chapter title for boundary detection
            next_ch_title = all_chapter_titles[ch_idx + 1] if ch_idx + 1 < len(all_chapter_titles) else None
            
            # Extract content for the whole chapter (is_chapter=True for smarter TOC skip)
            content, matched_title = extract_content_by_title(md_content, ch_title, next_ch_title, section_num=None, is_chapter=True)
            
            if content and len(content) > 100:
                conn.execute(
                    "INSERT INTO content_raw (subtopic_id, title, markdown_content) VALUES (?, ?, ?)",
                    (subtopic_id, ch_title, content)
                )
                content_count += 1
                if matched_title:
                    print(f"    [chapter-as-topic]: {ch_title[:40]}... ({len(content):,} chars) [fuzzy]")
                else:
                    print(f"    [chapter-as-topic]: {ch_title[:40]}... ({len(content):,} chars)")
            else:
                print(f"    [chapter-as-topic]: {ch_title[:40]}... (NO CONTENT)")
            
            continue  # Skip to next chapter
        
        # Process subtopics
        for st in ch.get('subtopics', []):
            st_num = st['number']
            st_title = st['title']
            
            # Parse subtopic order from section number
            try:
                subtopic_order = int(st_num.split('.')[-1])
            except (ValueError, IndexError):
                subtopic_order = subtopic_count + 1
            
            # Create subtopic
            subtopic_id = f"{topic_id}_{sanitize_id(st_title)}"
            conn.execute(
                "INSERT INTO subtopics (id, name, topic_id, order_num) VALUES (?, ?, ?, ?)",
                (subtopic_id, st_title, topic_id, subtopic_order)
            )
            subtopic_count += 1
            
            # Get next title for boundary
            global_idx = all_subtopics.index(st_title) if st_title in all_subtopics else -1
            next_title = all_subtopics[global_idx + 1] if global_idx >= 0 and global_idx + 1 < len(all_subtopics) else None
            
            # Extract content
            content = ""
            matched_title = None
            
            # Use line numbers if available (High Fidelity)
            if st.get('line_number'):
                start_l = st['line_number']
                
                # Determine end line
                # 1. Next subtopic in current chapter
                # 2. First subtopic of next chapter
                # 3. Next chapter start line
                # 4. End of file
                
                end_l = None
                # Check next subtopic in same chapter
                st_idx_in_ch = ch.get('subtopics', []).index(st)
                if st_idx_in_ch + 1 < len(ch.get('subtopics', [])):
                    end_l = ch['subtopics'][st_idx_in_ch + 1].get('line_number')
                
                # Check next chapter
                if not end_l and ch_idx + 1 < len(quality_report['chapters']):
                    next_ch = quality_report['chapters'][ch_idx + 1]
                    if next_ch.get('line_number'):
                        end_l = next_ch['line_number']
                
                if end_l:
                    content = extract_content_by_line_numbers(md_lines, start_l, end_l)
                else:
                    # Last subtopic in book
                    content = "\n".join(md_lines[start_l-1:]).strip()
            
            # Fallback to title-based extraction if line extraction failed or not available
            if not content:
                content, matched_title = extract_content_by_title(md_content, st_title, next_title, section_num=st_num)
            
            if content and len(content) > 100:
                conn.execute(
                    "INSERT INTO content_raw (subtopic_id, title, markdown_content) VALUES (?, ?, ?)",
                    (subtopic_id, st_title, content)
                )
                content_count += 1
                if matched_title:
                    print(f"    {st_num}: {st_title[:40]}... ({len(content):,} chars) [fuzzy]")
                else:
                    print(f"    {st_num}: {st_title[:40]}... ({len(content):,} chars)")
            else:
                print(f"    {st_num}: {st_title[:40]}... (NO CONTENT)")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Ingestion complete:")
    print(f"   Topics: {topic_count}")
    print(f"   Subtopics: {subtopic_count}")
    print(f"   Content: {content_count}/{subtopic_count} ({100*content_count/max(1,subtopic_count):.1f}%)")
    
    return {
        'subject_id': subject_id,
        'topics': topic_count,
        'subtopics': subtopic_count,
        'content': content_count
    }


# ============================================================
# STEP 4: Rewrite Content (Optional)
# ============================================================

def rewrite_content(subject_id: str, limit: int = None):
    """Rewrite raw content to educational HTML using Gemini API."""
    print("\n" + "="*60)
    print("STEP 3: Rewriting Content with LLM")
    print("="*60)
    
    conn = get_conn()
    
    # Get raw content that hasn't been processed
    query = """
        SELECT cr.id, cr.subtopic_id, cr.title, cr.markdown_content,
               s.name as subtopic_name, t.name as topic_name
        FROM content_raw cr
        JOIN subtopics s ON s.id = cr.subtopic_id
        JOIN topics t ON t.id = s.topic_id
        WHERE t.subject_id = ?
          AND NOT EXISTS (SELECT 1 FROM content_processed WHERE subtopic_id = cr.subtopic_id)
        ORDER BY t.order_num, s.order_num
    """
    if limit:
        query += f" LIMIT {limit}"
    
    rows = conn.execute(query, (subject_id,)).fetchall()
    
    if not rows:
        print("No content to rewrite (all already processed or no raw content)")
        conn.close()
        return
    
    print(f"Found {len(rows)} subtopics to rewrite...")
    
    success_count = 0
    error_count = 0
    
    for row in rows:
        raw_id = row['id']  # content_raw.id
        subtopic_id = row['subtopic_id']
        title = row['title']
        markdown = row['markdown_content']
        
        print(f"\n  Rewriting: {title[:50]}...")
        
        # Truncate if too long
        if len(markdown) > 30000:
            markdown = markdown[:30000] + "\n\n[Content truncated for processing]"
        
        prompt = f"""Transform this educational content into well-structured, interactive HTML for a tutoring system.

INPUT:
Title: {title}
Topic: {row['topic_name']}
Content:
{markdown}

OUTPUT REQUIREMENTS:
1. Clean, semantic HTML with Tailwind CSS classes
2. Include these sections:
   - Learning objectives (what students will learn)
   - Main content with clear explanations
   - Key concepts highlighted
   - Examples where appropriate
   - Summary/key takeaways
3. Make complex concepts accessible and engaging
4. Use proper heading hierarchy (h2, h3, h4)
5. Include visual formatting (lists, tables, callouts)

Return ONLY the HTML content, no markdown, no code fences."""

        messages = [
            {"role": "system", "content": "You are an expert educational content designer. Create engaging, well-structured HTML content."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = make_api_call(messages, max_tokens=8000, temperature=0.3, auto_fallback=True)
            
            if result['success'] and result['content']:
                html_content = result['content'].strip()
                
                # Clean up if wrapped in code fences
                if html_content.startswith('```'):
                    lines = html_content.split('\n')
                    html_content = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                
                # Insert processed content
                conn.execute(
                    "INSERT INTO content_processed (raw_id, subtopic_id, html_content, processor_version) VALUES (?, ?, ?, ?)",
                    (raw_id, subtopic_id, html_content, result.get('model', 'gemini'))
                )
                conn.commit()
                success_count += 1
                print(f"    ✅ Success ({len(html_content):,} chars)")
            else:
                error_count += 1
                print(f"    ❌ Error: {result.get('error', 'Unknown')}")
        except Exception as e:
            error_count += 1
            print(f"    ❌ Exception: {str(e)}")
    
    conn.close()
    
    print(f"\n✅ Rewriting complete:")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Automated Textbook Processing Pipeline')
    parser.add_argument('markdown_file', nargs='?', help='Path to markdown file (optional with --auto-discover)')
    parser.add_argument('--subject-name', help='Override subject name from LLM')
    parser.add_argument('--syllabus', default='CIE IGCSE', help='Syllabus name (default: CIE IGCSE)')
    parser.add_argument('--skip-rewrite', action='store_true', help='Skip the rewriting step')
    parser.add_argument('--rewrite-only', action='store_true', help='Only run rewriting (skip structure+ingest)')
    parser.add_argument('--rewrite-limit', type=int, help='Limit number of subtopics to rewrite')
    parser.add_argument('--subject-id', help='Subject ID for rewrite-only mode')
    parser.add_argument('--auto-discover', action='store_true', help='Auto-discover and process unprocessed markdown files')
    parser.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE_DIR, help='Source directory for auto-discovery')
    parser.add_argument('--list-only', action='store_true', help='Only list discovered files, do not process')
    parser.add_argument('--complete-rewrites', action='store_true', help='Complete any incomplete rewrites for existing subjects')
    
    args = parser.parse_args()
    
    # Auto-discovery mode
    if args.auto_discover or args.complete_rewrites:
        if args.list_only:
            # Just show what would be processed
            print("="*60)
            print("AUTO-DISCOVERY: LIST MODE")
            print("="*60)
            
            existing = get_existing_subjects()
            print(f"Existing subjects in DB: {len(existing)}")
            for s in sorted(existing):
                print(f"  - {s}")
            
            all_files = discover_markdown_files(args.source_dir)
            new_files = [f for f in all_files if f['subject_id'] not in existing]
            
            print(f"\nDiscovered markdown files: {len(all_files)}")
            print(f"New (unprocessed): {len(new_files)}")
            
            if new_files:
                print("\n--- Unprocessed Files ---")
                for f in new_files:
                    print(f"  - {f['subject_name']} ({f['syllabus']})")
                    print(f"    {f['path']}")
            
            incomplete = get_unprocessed_rewrites()
            if incomplete:
                print(f"\n--- Incomplete Rewrites ---")
                for subj, raw, proc in incomplete:
                    print(f"  - {subj}: {proc}/{raw}")
            
            return
        
        # Run auto-discovery and processing
        auto_discover_and_process(
            args.source_dir,
            skip_existing=not args.complete_rewrites,
            rewrite_incomplete=True
        )
        return
    
    # Rewrite-only mode
    if args.rewrite_only:
        if not args.subject_id:
            # Try to find subject by name pattern
            conn = get_conn()
            subject = conn.execute(
                "SELECT id FROM subjects WHERE id LIKE ? OR name LIKE ?",
                ('%ict%', '%ICT%')
            ).fetchone()
            conn.close()
            if subject:
                subject_id = subject['id']
            else:
                print("Error: --subject-id required for --rewrite-only mode")
                sys.exit(1)
        else:
            subject_id = args.subject_id
        
        rewrite_content(subject_id, limit=args.rewrite_limit)
        
        conn = get_conn()
        processed = conn.execute(
            "SELECT COUNT(*) FROM content_processed WHERE subtopic_id LIKE ?",
            (f"{subject_id}%",)
        ).fetchone()[0]
        conn.close()
        print(f"\nContent rewritten: {processed}")
        return
    
    # Single file mode - requires markdown_file argument
    if not args.markdown_file:
        print("Error: markdown_file required. Use --auto-discover to process all files.")
        print("\nUsage examples:")
        print("  python auto_process_textbook.py <markdown.md>  # Process single file")
        print("  python auto_process_textbook.py --auto-discover  # Auto-discover all")
        print("  python auto_process_textbook.py --auto-discover --list-only  # Just list files")
        print("  python auto_process_textbook.py --complete-rewrites  # Finish incomplete rewrites")
        sys.exit(1)
    
    markdown_path = Path(args.markdown_file)
    if not markdown_path.exists():
        print(f"Error: File not found: {args.markdown_file}")
        sys.exit(1)
    
    print("="*60)
    print("AUTOMATED TEXTBOOK PROCESSING PIPELINE")
    print("="*60)
    print(f"Input: {markdown_path.name}")
    print(f"Syllabus: {args.syllabus}")
    
    # Step 1: Generate quality report
    quality_report = generate_quality_report(markdown_path)
    
    # Step 2: Ingest content
    result = ingest_content(
        quality_report, 
        markdown_path, 
        subject_name=args.subject_name,
        syllabus=args.syllabus
    )
    
    # Step 3: Rewrite (optional)
    if not args.skip_rewrite:
        rewrite_content(result['subject_id'], limit=args.rewrite_limit)
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Subject: {result['subject_id']}")
    print(f"Topics: {result['topics']}")
    print(f"Subtopics: {result['subtopics']}")
    print(f"Content ingested: {result['content']}")
    
    if not args.skip_rewrite:
        conn = get_conn()
        processed = conn.execute(
            "SELECT COUNT(*) FROM content_processed WHERE subtopic_id LIKE ?",
            (f"{result['subject_id']}%",)
        ).fetchone()[0]
        conn.close()
        print(f"Content rewritten: {processed}")


if __name__ == '__main__':
    main()
