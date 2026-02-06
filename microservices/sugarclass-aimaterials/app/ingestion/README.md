# Ingestion Module

Manages raw content ingestion from PDF-to-Markdown conversion into the database.

## Purpose

This module handles the first stage of the content pipeline:
1. Parse quality reports (LLM-generated JSON files)
2. Extract content from markdown files using title-based search
3. Populate database tables (subjects, topics, subtopics, content_raw)
4. Track ingestion quality metrics

## Structure

```
app/ingestion/
├── __init__.py                  # Module initialization
├── create_quality_tables.py    # Create quality tracking tables
├── quality_tracker.py          # Quality tracking system
├── README.md                   # This file
└── utils/                      # Utility modules
    └── [future: markdown_extractor.py]
    └── [future: report_parser.py]
```

## Database Tables

### Main Tables
- `subjects` - Subject metadata
- `topics` - Chapters/units
- `subtopics` - Individual lessons
- `content_raw` - Original markdown content

### Quality Tracking Table
- `ingestion_quality` - Tracks ingestion status and quality metrics

## Usage

### Create Quality Tables
```bash
python app/ingestion/create_quality_tables.py
```

### Check Ingestion Status
```bash
python scripts/check_ingestion_status.py
```

## Quality Metrics

### Ingestion Quality Score (0-100)
- **Base: 50** points if content exists
- **+20** points if content > 1000 chars
- **+10** points if content > 5000 chars
- **+20** points if no errors/extraction issues

### Status Values
- `pending` - Waiting to be processed
- `ingested` - Successfully processed
- `failed` - Processing failed
- `needs_review` - Requires manual review

## Quality Tracker API

```python
from app.ingestion.quality_tracker import IngestionQualityTracker

tracker = IngestionQualityTracker()

# Start ingestion
tracker.start_ingestion(subtopic_id, subject_name)

# Record success
tracker.record_success(
    subtopic_id,
    content_length=10000,
    quality_score=85.5
)

# Record failure
tracker.record_failure(subtopic_id, "Error: Content not found")

# Get status
status = tracker.get_status(subtopic_id)

# Get statistics for a subject
stats = tracker.get_subject_stats("Business Studies (0450)")

# Get problematic items
problems = tracker.get_problematic_items(limit=10)
```

## Important Notes

1. **Title-Based Extraction**: Uses title search in markdown, not line numbers
2. **Quality Validation**: Automatic scoring based on content length
3. **Error Tracking**: All failures recorded with error messages
4. **Subject Segmentation**: Metrics tracked per subject

## Future Enhancements

- [ ] Move existing ingestion scripts to this module
- [ ] Implement markdown extractor utilities
- [ ] Implement report parser utilities
- [ ] Add batch processing capabilities
- [ ] Add progress reporting