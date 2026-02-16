# V8 Pipeline Implementation - Complete Replacement Guide

This document provides a complete guide for replacing the existing aimaterials pipeline with the V8 architecture.

---

## Overview

The V8 architecture replaces the old 3-stage pipeline (split → rewrite → exercises) with a more comprehensive system that generates 7 types of interactive content per subtopic.

### What Changed

| Aspect | Old System | New V8 System |
|--------|-----------|---------------|
| **Content Types** | 3 (Content, Exercise, QA) | 7 (Learn, Quiz, Cards, Real Life, Original) |
| **Visuals** | Static images | Animated SVGs |
| **Storage** | Separate content_raw/content_processed | Unified V8 tables |
| **Generation** | Manual per content type | Single background task |
| **Database** | Multiple tables | Streamlined V8 schema |

---

## File Structure

### Created Files

```
microservices/sugarclass-aimaterials/app/
├── schema_v8.sql                      # New database schema
├── admin_v8.py                        # New admin API endpoints
├── processors/
│   └── content_processor_v8.py       # New V8 content processor
└── frontend/src/
    ├── components/
    │   └── V8ContentView.jsx         # New V8 viewer component
    └── styles/
        └── v8-viewer.css              # V8 viewer styles
```

### Files to Modify

```
├── main.py                            # Add admin_v8 router
├── frontend/src/App.jsx               # Add V8 view mode
├── frontend/src/components/MiddleArea.orchestrator.jsx  # Add V8ContentView
└── frontend/src/index.jsx             # Import V8 styles
```

---

## Implementation Steps

### Step 1: Database Migration

```bash
# Backup existing database (optional, since we're replacing)
cd microservices/sugarclass-aimaterials/app
cp rag_content.db rag_content_backup.db

# Initialize new V8 schema
sqlite3 rag_content.db < schema_v8.sql
```

### Step 2: Backend Integration

Edit `main.py`:

```python
# Add import
from admin_v8 import router as admin_v8_router

# Include router
app.include_router(admin_v8_router)
```

### Step 3: Frontend Integration

Edit `frontend/src/App.jsx`:

```jsx
// Add V8 to view modes
const [viewMode, setViewMode] = useState('v8-learn'); // New default
```

Edit `frontend/src/components/MiddleArea.orchestrator.jsx`:

```jsx
// Add import
import V8ContentView from './V8ContentView';

// Add to content mode
if (viewMode === 'content') {
  // Check if subtopic has V8 content
  const hasV8Content = subtopic?.processed_at !== null;

  if (hasV8Content) {
    return <V8ContentView subtopicId={selectedSubtopicId} />;
  }

  // Fall back to legacy view
  return <LegacyContentView {...props} />;
}
```

Edit `frontend/src/index.jsx`:

```jsx
import './styles/v8-viewer.css';
```

### Step 4: Initial Content Import

```bash
# Process markdown files with V8 pipeline
cd microservices/sugarclass-aimaterials/app

# Process a single markdown file
python processors/content_processor_v8.py \
  --subject igcse_physics_0625 \
  --topic P1 \
  --file /path/to/markdown/P1-content.md

# Or process all files in a directory (create a loop script)
```

---

## Database Schema Overview

### Core Tables

```
syllabuses → subjects → topics → subtopics
```

### V8 Content Tables

```
v8_concepts          # 6-8 concepts per subtopic
v8_generated_content # SVG and bullet content
v8_quiz_questions    # 5 MCQs per subtopic
v8_flashcards        # 8 flashcards per subtopic
v8_reallife_images   # 3 real-life images per subtopic
v8_learning_objectives
v8_key_terms
v8_formulas
```

### Task Management

```
v8_processing_tasks  # Background generation tasks
v8_task_logs         # Task progress logs
```

---

## API Endpoints

### Subtopic Management

```
GET  /api/admin/v8/subjects
GET  /api/admin/v8/subjects/{subject_id}/topics
GET  /api/admin/v8/topics/{topic_id}/subtopics
GET  /api/admin/v8/subtopics/{subtopic_id}
GET  /api/admin/v8/subtopics/{subtopic_id}/status
```

### V8 Content Generation

```
POST /api/admin/v8/subtopics/{subtopic_id}/generate
     Request: { force_regenerate, generate_svgs, generate_quiz, ... }
     Response: { task_id, status, message }

GET  /api/admin/v8/tasks/{task_id}
     Response: { status, progress, message, logs, ... }
```

### Concept Management

```
PUT  /api/admin/v8/concepts/{concept_id}
     Request: { title, description, icon }

POST /api/admin/v8/concepts/{concept_id}/regenerate-svg
     Response: { task_id, status, message }
```

### Quiz Management

```
PUT  /api/admin/v8/quiz/{question_id}
     Request: { question_text, options, correct_answer, explanation }
```

---

## Frontend Components

### V8ContentView

Main component that displays V8 content with 7 view modes:

```jsx
<V8ContentView subtopicId={123} />
```

**Props:**
- `subtopicId` (number, required): Database ID of subtopic

**State:**
- `activeTab`: Current view mode ('learn', 'quiz', 'flashcards', 'reallife', 'original')
- `v8Data`: Loaded content from API
- `loading`, `error`: UI state

**View Modes:**

1. **Learn**: Concepts with SVGs and bullet points
2. **Quiz**: Interactive MCQ quiz with scoring
3. **Flashcards**: Flip cards for learning
4. **Real Life**: Real-life application images
5. **Original**: Source markdown content

### Sub-Components

- `V8LearnView`: Learning objectives, concepts, key terms, formulas
- `V8QuizView`: Interactive quiz with answer checking
- `V8FlashcardsView`: Flip card grid
- `V8RealLifeView`: Real-life application cards
- `V8OriginalView`: Original content display

---

## Content Generation Pipeline

### Automatic Generation

When you process a markdown file, the V8 processor:

1. **Parses markdown** into chapters/subtopics
2. **Analyzes structure** (identifies 6-8 concepts)
3. **Generates SVGs** for each concept
4. **Generates bullet points** for each concept
5. **Generates quiz** (5 MCQs)
6. **Generates flashcards** (8 cards)
7. **Saves all content** to database

### Manual Generation via API

```bash
# Trigger V8 content generation for a subtopic
curl -X POST "http://localhost:8004/api/admin/v8/subtopics/123/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "force_regenerate": false,
    "generate_svgs": true,
    "generate_quiz": true,
    "generate_flashcards": true,
    "generate_images": false
  }'

# Check task status
curl "http://localhost:8004/api/admin/v8/tasks/{task_id}"
```

### Background Task Flow

```
1. POST /subtopics/{id}/generate
   ↓
2. Create task record (status: pending)
   ↓
3. Background task starts
   ↓
4. Update progress (0-100%)
   ↓
5. Log each step
   ↓
6. Mark complete (status: completed)
```

---

## Configuration

### Environment Variables

```env
# Database
DB_PATH=/path/to/rag_content.db

# API Keys
GEMINI_API_KEY=your_api_key_here
GEMINI_API_URL=https://hb.dockerspeeds.asia/v1/chat/completions

# API Settings
GEMINI_MODEL=gemini-2.5-flash
REQUEST_INTERVAL=6.0  # 10 requests per minute
MAX_RETRIES=3
REQUEST_TIMEOUT=120
```

### API Key File

Create or update `coding/api/api.txt`:

```
key: your_gemini_api_key_here
```

---

## CSS Variables

The V8 viewer uses CSS variables for theming. Override in your global styles:

```css
:root {
  --primary: #be123c;
  --primary-hover: #9f1239;
  --primary-bg: #fff1f2;

  --secondary: #0369a1;
  --secondary-bg: #e0f2fe;

  --success: #059669;
  --success-bg: #d1fae5;

  --warning: #d97706;
  --warning-bg: #fef3c7;

  --bg-body: #f8fafc;
  --bg-card: #ffffff;

  --border: #e2e8f0;

  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-light: #94a3b8;

  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  --radius: 12px;
}
```

---

## Testing the Installation

### 1. Verify Database Schema

```bash
sqlite3 rag_content.db ".schema" | grep v8
```

Should show: `v8_concepts`, `v8_generated_content`, `v8_quiz_questions`, etc.

### 2. Test API Endpoints

```bash
# List subjects
curl http://localhost:8004/api/admin/v8/subjects

# Get subtopic status
curl http://localhost:8004/api/admin/v8/subtopics/1/status
```

### 3. Test Frontend

1. Start the aimaterials service
2. Navigate to a subtopic with V8 content
3. Should see V8 tab bar with 7 view modes
4. Test each view mode

---

## Migration from Old System

### Data Migration Script

Create a migration script to move existing content:

```python
# migrate_to_v8.py

import sqlite3
from pathlib import Path

DB_PATH = "rag_content.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Migrate subtopics
    cursor.execute("""
        INSERT INTO subtopics_v8 (topic_id, subtopic_id, slug, name, order_num)
        SELECT
            t.id as topic_id,
            s.subtopic_id,
            LOWER(REPLACE(REPLACE(s.name, ' ', '-'), '/', '')) as slug,
            s.name,
            s.order_num
        FROM subtopics_old s
        JOIN topics_old t ON s.topic_id = t.id
    """)

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
```

---

## Troubleshooting

### Issue: V8 content not displaying

**Check:**
1. Subtopic has `processed_at` timestamp in database
2. V8 tables have content for the subtopic
3. API endpoint returns data

```bash
sqlite3 rag_content.db "SELECT processed_at FROM subtopics WHERE id = 123"
sqlite3 rag_content.db "SELECT COUNT(*) FROM v8_concepts WHERE subtopic_id = 123"
```

### Issue: SVG generation fails

**Check:**
1. API key is valid
2. API endpoint is accessible
3. Rate limiting is working

```bash
# Test API directly
curl -X POST "https://hb.dockerspeeds.asia/v1/chat/completions" \
  -H "Authorization: Bearer $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": "test"}]}'
```

### Issue: Background task stuck

**Check:**
1. Task status in database
2. Task logs for errors

```bash
sqlite3 rag_content.db "SELECT status, message FROM v8_processing_tasks WHERE task_id = 'xxx'"
sqlite3 rag_content.db "SELECT * FROM v8_task_logs WHERE task_id = 'xxx' ORDER BY created_at DESC LIMIT 10"
```

---

## Performance Optimization

### Caching

- V8 content is cached in database after generation
- Subtopic `source_hash` prevents re-processing unchanged content
- Generated SVGs are stored, not regenerated

### Rate Limiting

- Default: 10 requests per minute (6 second intervals)
- Configurable via `REQUEST_INTERVAL` environment variable
- Respects API rate limits to avoid 429 errors

### Background Tasks

- Long operations run in background threads
- Progress tracking via database
- Logs stored for debugging

---

## Next Steps

1. **Deploy schema changes** to production database
2. **Update backend** to include V8 router
3. **Update frontend** with V8 components
4. **Process existing content** with V8 pipeline
5. **Test thoroughly** before rolling out to users
6. **Monitor API usage** and adjust rate limits if needed

---

## Support

For issues or questions:
1. Check the logs in `v8_task_logs` table
2. Review the task status in `v8_processing_tasks` table
3. Verify API configuration and credentials
4. Check that markdown files are accessible

---

## Summary

The V8 pipeline provides a complete replacement for the old aimaterials system with:

- ✅ Unified database schema
- ✅ Automated content generation
- ✅ Interactive 7-view frontend
- ✅ Background task processing
- ✅ Progress tracking and logging
- ✅ Admin panel integration
- ✅ No backward compatibility needed

All files have been created and are ready for integration into the existing Sugarclass.app aimaterials service.
