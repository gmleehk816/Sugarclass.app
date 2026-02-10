# AI Materials Microservice

**AI Materials** is a specialized microservice within the Sugarclass ecosystem that provides students with enhanced educational content and AI-generated exercises.

## 🏗 Architecture

This service is built as a standalone **FastAPI** application that is embedded via an iframe into the Sugarclass Shell dashboard.

- **Primary Entry Point**: `app/main.py`
- **Port**: `8004`
- **Database**: SQLite (`rag_content.db`) shared with the AI Tutor service.
- **LLM Integration**: Uses specialized AI models for content rewriting and exercise generation.

## 🚀 Quick Start

### 1. Environment Configuration
Create a `.env` file based on `.env.example`:
```env
# Application Settings
DEBUG=False
PORT=8004

# Database
DB_PATH=/app/database/rag_content.db

# LLM API
LLM_API_URL=https://hb.dockerspeeds.asia/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gemini-1.5-flash
```

### 2. Run with Docker
The service is best run via the root `docker-compose.yml`:
```bash
docker compose up -d --build aimaterials-backend
```

## 📚 Key Features

### 1. Exercise & Question CRUD
Complete management of educational exercises through the Admin Panel.
- **Manual CRUD**: Create, Update, Delete questions.
- **AI Generation**: Generate single or batch questions for any subtopic.
- **Content Splitting**: Automatically processes textbook content into teachable subtopics.

### 2. Content Enhancement
- **Markdown Processing**: Converts raw textbook data into rich, styled HTML.
- **Image Generation**: Automatically generates educational diagrams via AI.

## 🛣 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8004/docs`
- **ReDoc**: `http://localhost:8004/redoc`

### Standard Endpoints
- `GET /health` - Service health check.
- `GET /api/topics` - List all educational topics.
- `POST /api/admin/generate-exercises` - Trigger background generation.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite
- **LLM Communication**: standard OpenAI-compatible messages API
- **Processing**: Pydantic, markdown-it, requests

---
*Sugarclass Engineering Team*
