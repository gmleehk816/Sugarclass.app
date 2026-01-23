# SugarClass - AI Tutor RAG System

**SugarClass** is an advanced AI Tutor system designed to deliver high-quality, hallucination-free educational assistance. It employs a **Retrieval-Augmented Generation (RAG)** architecture to ground its answers in specific syllabus content (e.g., IGCSE, A-Level), ensuring that students receive accurate explanations directly referenced from their course materials.

This project is a **monorepo** containing a React-based frontend, a Python/FastAPI backend, and a specialized synchronization engine for data management.

---

## 🏗 System Architecture

The system is built on a **microservices-inspired** architecture orchestrated via Docker Compose:

### 1. **Core Backend (`tutor-service`)**
- **Framework**: FastAPI + Uvicorn.
- **Agent Orchestration**: LangChain & LangGraph.
- **AI Model**: Google Gemini 1.5 (via `langchain-google-genai`) or OpenAI-compatible models.
- **Responsibility**: Handles student sessions, generates answers using RAG, and serves API endpoints.
- **Key Logic**: `services/rag_service/tutor_main.py`

### 2. **Data Sync Engine (`sync-agent`)**
- **Role**: The "Source of Truth" manager.
- **Workflow**:
    1.  Monitors the **Source SQLite DB** (`database/rag_content.db`) for changes.
    2.  Migrates data to the **PostgreSQL Content DB**.
    3.  Embeds content chunks (using BAAI/bge-small-en-v1.5).
    4.  Upserts vectors into **Qdrant**.
- **Key Logic**: `services/rag_service/sync/sync_manager.py`

### 3. **Frontend (`tutor-frontend`)**
- **Framework**: React 18, Vite, TypeScript.
- **Styling**: TailwindCSS + Custom CSS animations.
- **Features**: Chat interface, file uploads, subject selection, and real-time citation rendering.
- **Entry Point**: `frontend/src/App.tsx`

### 4. **Infrastructure Services**
- **Qdrant**: Vector database for semantic search.
- **PostgreSQL**:
    - `content-db`: Stores structured syllabus content (chapters, topics, text).
    - `agent-db`: Stores user profiles, sessions, and chat history.
- **Redis**: Caching layer for high-speed query responses and session management.
- **Nginx**: Reverse proxy serving the frontend and routing `/api` requests to the backend.

---

## 🛠 Tech Stack Details

| Component | Technology | Description |
| :--- | :--- | :--- |
| **LLM** | **Google Gemini 1.5** | Primary reasoning engine. Can act as a tutor, quiz generator, or grader. |
| **Embeddings** | `BAAI/bge-small-en-v1.5` | High-performance embedding model for educational content semantic search. |
| **Vector DB** | **Qdrant** | Stores document embeddings for retrieval. |
| **Database** | **PostgreSQL 15** | Dual-database setup for separation of concerns (Content vs. User Data). |
| **Orchestration** | **Docker Compose** | Manages the lifecycle of all 7 containers. |
| **Frontend** | **React + Vite** | High-performance SPA with a focus on "Premium Interactions" (animations, glassmorphism). |

---

## � Project Structure (Cleaned)

```bash
g:/PROGRAMMING/Projects/sugarclass.app/
├── 📄 .env.prod                # Production environment variables (API Keys, Passwords)
├── 📄 docker-compose.tutor.yml # Main orchestration file for all services
├── 📄 Dockerfile.tutor         # Unified Python image for Backend & Sync Agent
├── 📂 database/                # Contains the source SQLite file (rag_content.db) & migrations
├── 📂 frontend/                # React application source code
├── 📂 scripts/                 # Utility scripts (Deployment, Manual Sync)
│   ├── deploy.sh               # Automated VPS deployment script
│   └── migrate_sqlite_to_postgres.py
└── 📂 services/
    └── 📂 rag_service/         # Main Python codebase
        ├── 📂 agents/          # LangGraph agents (Quiz, Retriever, etc.)
        ├── 📂 api/             # FastAPI route definitions
        ├── 📂 database/        # DB connection logic and schema management
        └── 📄 tutor_main.py    # Application entry point
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Docker Desktop** installed and running.
- **Google API Key** (for Gemini).

### 2. Environment Setup
1. Copy the example env file:
   ```bash
   cp .env.prod.example .env.prod
   ```
2. Edit `.env.prod`:
   - Set `GOOGLE_API_KEY=your_key_here`.
   - Set database passwords (defaults are usually fine for local dev).

### 3. Launch
```bash
docker-compose -f docker-compose.tutor.yml up -d --build
```
*Wait for ~2-3 minutes for the Sync Agent to perform the initial migration and vectorization.*

### 4. Access
- **Web Interface**: [http://localhost:3000](http://localhost:3000)
- **API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 🤖 Context for AI Assistants

If you are an AI assistant helping with this project, here is what you need to know:
1. **Source of Truth**: The content flow is **One-Way**: `SQLite` -> `PostgreSQL` -> `Qdrant`. Do NOT try to insert content directly into Qdrant or Postgres without going through the Sync/Migration logic.
2. **Subject Context**: The frontend strictly enforces **Subject Locking**. If a user selects "Physics", the ID of the physics syllabus is passed to the backend, and the RAG retriever filters *only* for physics content.
3. **State Management**: The frontend uses **Immutable State Updates** for the chat history to prevent rendering crashes. Always use `setChatHistory(prev => ...)` patterns.
4. **No Streaming**: The system currently uses standard HTTP Request/Response for stability. Streaming logic has been removed.

---

## 📝 Maintenance & Deployment

- **Manual Sync**: If you add a new file to `database/rag_content.db`, the `sync-agent` should detect it automatically. To force run:
  ```bash
  docker restart tutor-sync-agent
  ```
- **VPS Deployment**:
  Run the automated script on your Ubuntu server:
  ```bash
  sudo ./scripts/deploy.sh
  ```

---
*Maintained by the SugarClass Engineering Team.*
