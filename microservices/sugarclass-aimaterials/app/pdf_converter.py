"""
PDF to Markdown Converter using pymupdf4llm

Provides text-only extraction from PDFs for the AI Materials system.
Images from PDFs are not extracted - new AI-generated images (SVGs)
are created during content processing.
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def is_pdf_file(file_path: Path) -> bool:
    """Check if file is a PDF based on extension."""
    return file_path.suffix.lower() == '.pdf'


def convert_pdf_to_markdown(
    pdf_path: Path,
    output_dir: Optional[Path] = None
) -> Tuple[str, Optional[Path]]:
    """
    Convert a PDF file to markdown using pymupdf4llm.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the markdown file (optional)

    Returns:
        Tuple of (markdown_content, output_path)

    Raises:
        ImportError: If pymupdf4llm is not installed
        ValueError: If the PDF file doesn't exist
        Exception: If conversion fails
    """
    try:
        import pymupdf4llm
    except ImportError:
        raise ImportError(
            "pymupdf4llm is not installed. "
            "Install it with: pip install pymupdf4llm"
        )

    if not pdf_path.exists():
        raise ValueError(f"PDF file not found: {pdf_path}")

    # Convert PDF to markdown (text-only extraction)
    md_text = pymupdf4llm.to_markdown(str(pdf_path))

    output_path = None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{pdf_path.stem}.md"
        output_path.write_text(md_text, encoding='utf-8')

    return md_text, output_path


# ---------------------------------------------------------------------------
# PDF TOC / Bookmark extraction
# ---------------------------------------------------------------------------

# Headings that are structural noise, not real chapters
_NOISE_TITLES = {
    'table of contents', 'contents', 'toc', 'index', 'glossary',
    'bibliography', 'references', 'appendix', 'appendices',
    'acknowledgements', 'acknowledgments', 'preface', 'foreword',
    'about the author', 'about the authors', 'copyright',
    'dedication', 'cover', 'title page', 'half title',
}


def extract_toc(pdf_path: Path) -> List[Dict]:
    """
    Extract the Table of Contents (bookmarks/outlines) from a PDF.

    Uses PyMuPDF's ``doc.get_toc()`` which reads the PDF outline tree.
    Most published textbooks embed this metadata — it is the single most
    reliable source of chapter structure.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of dicts ``{level: int, title: str, page: int}`` ordered by
        appearance.  ``level=1`` → top-level chapter, ``level=2`` → section,
        ``level=3`` → subsection, etc.  Only entries containing at least one
        letter are returned (pure page-number entries are filtered out).

    Raises:
        ImportError: If PyMuPDF (``fitz``) is not installed.
        ValueError: If the PDF does not exist.
    """
    try:
        import fitz  # PyMuPDF — ships with pymupdf4llm
    except ImportError:
        raise ImportError("PyMuPDF (fitz) is required. Install with: pip install pymupdf")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise ValueError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    raw_toc = doc.get_toc()  # list of [level, title, page_number]
    doc.close()

    if not raw_toc:
        return []

    entries: List[Dict] = []
    for level, title, page in raw_toc:
        title = (title or "").strip()

        # Skip empty or page-number-only entries
        if not title or not re.search(r'[A-Za-z]', title):
            continue

        # Skip structural noise
        if title.lower().strip() in _NOISE_TITLES:
            continue

        # Strip trailing page numbers that sometimes appear in the bookmark text
        title = re.sub(r'\s+\d{1,4}\s*$', '', title).strip()
        if not title:
            continue

        entries.append({
            'level': int(level),
            'title': title,
            'page': int(page),
        })

    return entries

