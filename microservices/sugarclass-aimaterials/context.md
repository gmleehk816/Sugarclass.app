# Technical Context: AI Materials

This document provides technical details for AI agents working on the AI Materials microservice.

## 🗄 Database Schema (`rag_content.db`)

The service uses a centralized SQLite database. Key tables include:

### 🎓 Educational Hierarchy
- `syllabuses`: Root of the hierarchy.
- `subjects`: Standard subjects (e.g., ib_dp_chemistry).
- `topics`: Chapters or major modules.
- `subtopics`: The smallest teachable unit, where content is attached.

### 📝 Content & Processing
- `content_raw`: Stores raw markdown extracted from textbooks.
- `content_processed`: Stores enhanced HTML with AI-generated images and summarized metadata.
- `exercises`: Parent table for exercise sets (linked to `subtopics`).
- `questions`: Individual exercise items (linked to `exercises`).

## ⚙️ Processing Pipeline

1. **Splitting** (`processors/content_splitter.py`):
   - Reads raw text/markdown.
   - Uses regex to split into subtopics based on numbered headings (e.g., "1.1 Hardware").
   - Populates `subtopics` and `content_raw`.

2. **Enhancement** (`processors/content_rewriter_with_images.py`):
   - Analyzes raw content.
   - Generates educational images via LLM/Diffusion.
   - Rewrites Markdown into styled HTML.
   - Populates `content_processed`.

3. **Exercise Generation** (`exercise_builder.py`):
   - Triggers from `admin.py` or manually.
   - Reads from `content_raw` (RAG source).
   - Generates JSON-structured questions (text + options).
   - Saves to `exercises` and `questions`.

## 🛠 Key Files & Roles

- `app/main.py`: FastAPI application, core API routes, static file serving.
- `app/admin.py`: Bulk processing management, manual exercise CRUD, background task orchestration.
- `app/exercise_builder.py`: Content-to-exercise generation logic.
- `app/config_fastapi.py`: Environment-based settings (Pydantic).

## ⚠️ Important Constraints

1. **DB Path**: Always use the path provided in the `.env` (typically `/app/database/rag_content.db` in Docker).
2. **Iframe Shell**: The frontend uses `postMessage` to send auth tokens.
3. **Images**: Generated images are stored in `app/static/generated_images/`.
