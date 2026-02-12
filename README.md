# Sugarclass - AI Learning Orchestrator

**Sugarclass** is a premium, institutional-grade learning orchestrator designed for kids and young students aged 7-18. It serves as a "Mission Control" hub that integrates multiple specialized AI tools into a unified, secure, and engaging environment.

---

## 🏗 Architecture Overview

The project uses a **Shell + Module** architecture where separate AI-powered microservices are embedded into a central dashboard via iframes.

```
sugarclass.app/
├── backend/                    # Main Dashboard API (FastAPI + SQLite)
├── frontend/                   # Main Dashboard UI (Next.js)
└── microservices/
    ├── sugarclass-aiwriter/    # News-based AI Writing Assistant
    ├── sugarclass-aitutor/     # RAG-based AI Tutor
    ├── sugarclass-aiexaminer/  # AI-powered Exam Preparation
    └── sugarclass-aimaterials/ # AI-powered Materials & Exercises
```

### Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| **Dashboard Frontend** | 3400 | Main shell/hub UI |
| **Dashboard Backend** | 8000 | User auth, progress tracking |
| **AI Writer Frontend** | 3401 | Writing assistant UI |
| **AI Writer Backend** | 8001 | News collection, AI drafts |
| **AI Tutor Frontend** | 3402 | Tutoring system UI |
| **AI Tutor Backend** | 8002 | RAG tutoring, quizzes |
| **AI Examiner Frontend** | 3403 | Exam preparation UI |
| **AI Examiner Backend** | 8003 | Material upload, quiz generation |
| **AI Materials Backend** | 8004 | Enhanced content, Exercise CRUD |
| **AI Writer DB (Postgres)** | 5602 | News/drafts storage |
| **AI Tutor Content DB** | 5600 | Syllabus content |
| **AI Tutor Agent DB** | 5601 | Sessions, mastery |
| **Qdrant (Vector DB)** | 6333 | Semantic search |
| **Redis** | 6379 | Caching |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git

### 1. Clone & Setup Environment

```bash
# Ensure you have the .env file for aiwriter
cp microservices/sugarclass-aiwriter/.env.example microservices/sugarclass-aiwriter/.env

# Ensure you have the .env.prod for aitutor
cp microservices/sugarclass-aitutor/.env.prod.example microservices/sugarclass-aitutor/.env.prod

# Ensure you have the .env for aiexaminer
cp microservices/sugarclass-aiexaminer/.env.example microservices/sugarclass-aiexaminer/.env

# Ensure you have the .env for aimaterials
cp microservices/sugarclass-aimaterials/.env.example microservices/sugarclass-aimaterials/.env
```

### 2. Start All Services

```bash
docker-compose up -d --build
```

### 3. Access the Platform

- **Dashboard**: http://localhost:3400
- **AI Writer**: http://localhost:3401/aiwriter
- **AI Tutor**: http://localhost:3402/aitutor
- **AI Examiner**: http://localhost:3403/examiner
- **AI Materials**: http://localhost:8004 (Embedded)
- **AI Tutor API**: http://localhost:8002/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## 📂 Microservice Details

### AI Writer (`microservices/sugarclass-aiwriter/`)
A news-based writing platform that:
- Collects age-appropriate news articles
- Generates AI-powered writing prompts
- Helps students practice essay and article writing
- Provides feedback and suggestions

### AI Tutor (`microservices/sugarclass-aitutor/`)
A RAG-based tutoring system that:
- Uses syllabus-specific content (IGCSE, A-Level, etc.)
- Provides contextual Q&A from educational materials
- Tracks student mastery and generates quizzes
- Features automatic content synchronization
- Supports semantic search via Qdrant vector database

### AI Examiner (`microservices/sugarclass-aiexaminer/`)
An AI-powered exam preparation platform that:
- Uploads PDF/image materials and organizes them into folders
- Generates multiple-choice and short-answer questions via AI
- Provides complete question editing capabilities
- Manages materials and folders (rename, delete, add files)
- Tracks student practice and progress
- Features teacher-friendly customization tools

### AI Materials (`microservices/sugarclass-aimaterials/`)
An AI-powered content enhancement service that:
- Rewrites textbook content into structured HTML/SVG
- Generates educational images via Diffusion models
- Provides a full Admin CRUD for exercises and questions
- Features content regeneration with customizable options (focus, temperature, sections)
- Includes content browser with subject/topic/subtopic navigation
- Supports background task processing with progress tracking

---

## 🔧 Development

### Running Individual Microservices

**AI Writer (standalone):**
```bash
cd microservices/sugarclass-aiwriter
docker-compose up -d --build
```

**AI Tutor (standalone):**
```bash
cd microservices/sugarclass-aitutor
docker-compose -f docker-compose.tutor.yml up -d --build
```

**AI Examiner (standalone):**
```bash
cd microservices/sugarclass-aiexaminer
docker-compose up -d --build
```

**AI Materials (standalone):**
```bash
cd microservices/sugarclass-aimaterials
docker-compose up -d --build
```

### Stop All Services
```bash
docker-compose down
```

---

## 🤖 Context for AI Assistants

1. **Shell Architecture**: The main dashboard hosts child apps via `<ServiceFrame>` iframes.
2. **SSO Handshake**: The shell sends tokens to iframes via `postMessage`.
3. **Microservice Paths**: All microservices are in `./microservices/{service-name}/`.
4. **Database Isolation**: Each microservice has its own database (no shared state).
5. **Port Mapping**: Dashboard=8000/3400, Writer=8001/3401, Tutor=8002/3402, Examiner=8003/3403, Materials=8004/3404.

---

## 🌟 Recent Features

### AI Examiner Teacher Customization
- Material management with folder organization
- Complete question editing (CRUD operations)
- Folder management (create, rename, add files, delete)
- Auto-naming from material filenames
- Student progress tracking

### AI Materials Content Management
- Content edit modal for HTML content, summary, and key terms
- Content regeneration modal with AI customization options
- Content browser component with tree view navigation
- Backend CRUD API for content management
- LLM-powered content regeneration with background tasks

### AI Tutor Enhancements
- Full frontend interface with React/Vite
- Data sync agent for automatic content updates
- Enhanced RAG capabilities with Qdrant integration
- Session management with Redis caching

---

## 🌐 Deployment to VPS

### 1. Initial Setup
Run the setup script on your VPS:
```bash
curl -sSL https://raw.githubusercontent.com/gmleehk816/Sugarclass.app/main/setup-vps.sh | bash
```

### 2. Configure SSL
Generate SSL certificates using Certbot:
```bash
sudo docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email your-email@example.com --agree-tos --no-eff-email -d sugarclass.app -d www.sugarclass.app
```

### 3. Update Nginx for SSL
After generating certificates, uncomment the SSL redirect and port 443 block in `gateway/nginx/nginx.conf` and restart:
```bash
sudo docker compose -f docker-compose.prod.yml restart gateway
```

---

*Maintained by the Sugarclass Engineering Team.*
