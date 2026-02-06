# Build Knowledge Base Scripts

Scripts for processing Markdown files into the SQLite knowledge base.

## Pipeline Overview

```
PDF → Markdown → Split by Topic → Parse Q&A → SQLite DB → AI Tutor
     (pdf_conversion)  (content_builder)
```

## Scripts

### Content Splitting
- `split_chemistry.py` - Split Chemistry textbook by chapters/topics
- `split_coursebook.py` - Split Combined Science coursebook
- `split_cs_textbook.py` - Split Computer Science textbook
- `resplit_coursebook.py` - Re-split with improved logic

### Content Building
- `build_content.py` - Process markdown files and enhance them with AI images
- `parse_qa.py` - Parse Q&A content from markdown
- `consolidate_subjects.py` - Consolidate subject data
- `split_*.py` - Various scripts to split textbooks into chapters/subtopics

### Full Pipeline
- `full_pipeline.py` - Complete pipeline from PDF to database

## Usage

```bash
# Split a textbook markdown into topics
python content_builder/split_chemistry.py

# Build content from split markdown
python content_builder/build_content.py

# Parse Q&A sections
python content_builder/parse_qa.py

# Or run full pipeline
python content_builder/full_pipeline.py
```

## Database Schema

The scripts populate `rag_content.db` with:
- Topics and subtopics
- Content sections
- Questions and answers
- Image references
