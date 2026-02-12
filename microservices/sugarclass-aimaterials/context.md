# Technical Context: AI Materials

This document provides technical details for AI agents working on the AI Materials microservice.

## 🏗 Architecture Overview

AI Materials is a FastAPI-based microservice within the Sugarclass ecosystem that provides:
- Enhanced educational content with AI-generated images
- Complete CRUD operations for exercises and questions
- Content regeneration with customizable LLM parameters
- Admin panel for content management
- Integration with the main Sugarclass orchestrator via iframe

**Port**: 8004
**Database**: SQLite (`rag_content.db`) - shared with AI Tutor service
**Frontend**: React/Vite (served at port 3404)

## 🗄 Database Schema (`rag_content.db`)

The service uses a centralized SQLite database. Key tables include:

### 🎓 Educational Hierarchy
- `syllabuses`: Root of the hierarchy (e.g., IGCSE, A-Level, IB)
- `subjects`: Standard subjects (e.g., ib_dp_chemistry, igcse_physics)
- `topics`: Chapters or major modules within subjects
- `subtopics`: The smallest teachable unit, where content is attached

### 📝 Content & Processing
- `content_raw`: Stores raw markdown extracted from textbooks
  - Fields: `id`, `subtopic_id`, `markdown_content`, `title`, `created_at`
- `content_processed`: Stores enhanced HTML with AI-generated images and metadata
  - Fields: `id`, `subtopic_id`, `html_content`, `summary`, `key_terms`, `processor_version`, `processed_at`
- `exercises`: Parent table for exercise sets (linked to `subtopics`)
  - Fields: `id`, `subtopic_id`, `title`, `difficulty`, `created_at`
- `questions`: Individual exercise items (linked to `exercises`)
  - Fields: `id`, `exercise_id`, `question_text`, `question_type`, `options` (JSON), `correct_answer`, `explanation`

## ⚙️ Processing Pipeline

### 1. Content Splitting (`processors/content_splitter.py`)
- Reads raw text/markdown from textbook PDFs
- Uses regex to split into subtopics based on numbered headings (e.g., "1.1 Hardware")
- Populates `subtopics` and `content_raw` tables
- Maintains hierarchical structure (syllabus → subject → topic → subtopic)

### 2. Content Enhancement (`processors/content_rewriter_with_images.py`)
- Analyzes raw markdown content
- Generates educational images via LLM/Diffusion models
- Rewrites Markdown into styled, structured HTML
- Adds metadata: summary, key terms, learning objectives
- Populates `content_processed` table
- Stores images in `app/static/generated_images/`

### 3. Exercise Generation (`exercise_builder.py`)
- Triggers from admin panel or API endpoints
- Reads from `content_raw` (RAG source)
- Generates JSON-structured questions with multiple formats:
  - Multiple choice (with 4 options)
  - Short answer
  - True/False
- Saves to `exercises` and `questions` tables
- Supports batch generation for entire topics

## 🆕 Recent Features (2026-02)

### Content Management System
- **Content Edit Modal**: Edit HTML content, summary, and key terms directly
- **Content Regeneration Modal**: AI-powered regeneration with customizable options:
  - Focus areas (specific topics to emphasize)
  - Temperature control (creativity level)
  - Section selection (regenerate specific parts)
- **Content Browser Component**: Tree view navigation by subject/topic/subtopic
- **Background Task Processing**: Long-running regeneration tasks with progress tracking

### Admin API Endpoints
- `GET /api/admin/contents` - List all content with filtering
- `GET /api/admin/contents/{subtopic_id}` - Get specific content
- `PUT /api/admin/contents/{subtopic_id}` - Update content
- `DELETE /api/admin/contents/{subtopic_id}` - Delete content
- `POST /api/admin/contents/{subtopic_id}/regenerate` - Trigger AI regeneration
- `GET /api/admin/regenerate/status/{task_id}` - Check regeneration progress

### Exercise CRUD
- `GET /api/exercises/{subtopic_id}` - Get exercises for a subtopic
- `POST /api/admin/exercises` - Create new exercise
- `PUT /api/admin/exercises/{exercise_id}` - Update exercise
- `DELETE /api/admin/exercises/{exercise_id}` - Delete exercise
- `POST /api/admin/generate-exercises` - Batch generate exercises

## 🛠 Key Files & Roles

### Core Application
- `app/main.py`: FastAPI application, core API routes, static file serving
- `app/admin.py`: Admin router with CRUD operations, background task orchestration
- `app/config_fastapi.py`: Environment-based settings (Pydantic)
- `app/creative_rewriter_service.py`: LLM-powered content regeneration service

### Processing & Generation
- `app/exercise_builder.py`: Content-to-exercise generation logic
- `app/processors/content_splitter.py`: Textbook content splitting
- `app/processors/content_rewriter_with_images.py`: Content enhancement with images

### Frontend
- `app/frontend/`: React/Vite application for admin panel
- `app/static/`: Static assets and generated images

## 🔌 Integration Points

### With Main Orchestrator
- Embedded via iframe in the main Sugarclass dashboard
- Receives authentication tokens via `postMessage` API
- Shares user session with parent shell

### With AI Tutor
- Shares the same `rag_content.db` database
- Content processed here is used by AI Tutor for RAG queries
- Exercises generated here can be used in tutoring sessions

## ⚠️ Important Constraints

1. **DB Path**: Always use the path provided in the `.env` file
   - Development: `./database/rag_content.db`
   - Docker: `/app/database/rag_content.db`

2. **Iframe Communication**: The frontend uses `postMessage` to send auth tokens from parent shell

3. **Image Storage**: Generated images are stored in `app/static/generated_images/`
   - Must be accessible via `/generated_images/` URL path
   - Images are referenced in HTML content by relative paths

4. **LLM Configuration**:
   - API URL and key configured in `.env`
   - Supports OpenAI-compatible APIs
   - Model selection: `LLM_MODEL` environment variable

5. **Background Tasks**:
   - Long-running operations (regeneration, batch generation) use FastAPI BackgroundTasks
   - Progress tracked via in-memory state or database
   - Client polls for status updates

## 🔧 Development Notes

### Running Standalone
```bash
cd microservices/sugarclass-aimaterials
docker-compose up -d --build
```

### Environment Variables
```env
DEBUG=False
PORT=8004
DB_PATH=/app/database/rag_content.db
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4
```

### API Documentation
- Swagger UI: `http://localhost:8004/docs`
- ReDoc: `http://localhost:8004/redoc`

### Database Migrations
- No formal migration system currently
- Schema changes handled via `content_splitter.init_database()`
- Manual SQL scripts in `database/migrations/` (if needed)

## 📊 Performance Considerations

- **Content Regeneration**: Can take 30-60 seconds per subtopic
- **Image Generation**: Additional 10-20 seconds per image
- **Batch Operations**: Use background tasks to avoid timeout
- **Database**: SQLite is sufficient for current scale (<10k subtopics)
- **Caching**: Consider Redis for frequently accessed content (future enhancement)

---
*Last Updated: 2026-02-12*
