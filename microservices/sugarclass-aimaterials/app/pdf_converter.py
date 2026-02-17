"""
PDF to Markdown Converter using pymupdf4llm

Provides text-only extraction from PDFs for the AI Materials system.
Images from PDFs are not extracted - new AI-generated images (SVGs)
are created during content processing.
"""
from pathlib import Path
from typing import Optional, Tuple


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
