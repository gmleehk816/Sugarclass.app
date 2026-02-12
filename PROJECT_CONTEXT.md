# Project Context: Sugarclass AI Learning Orchestrator

## 1. Overview
**Sugarclass** is a premium, institutional-grade learning orchestrator designed for kids and young students. It serves as a "Mission Control" hub that integrates multiple specialized AI tools into a unified, secure, and engaging environment.

- **Primary Goal**: To provide a safe, smart, and beautiful workspace where students can read news, write stories, ask AI teachers for help, practice with exercises, and test their knowledge.
- **Target Audience**: Students ages 7-18, teachers, and educational institutions.
- **Design Aesthetic**: "Slate & Ivory" – A clean, high-end professional look that feels like an "Enterprise for Kids" platform. High use of glassmorphism, fluid animations (Framer Motion), and premium iconography (Lucide).

---

## 2. Core Architecture: "Shell & Module"
The application is built using a **Micro-Frontend/Service Architecture** integrated via a secure Iframe Shell.

### The Shell (Dashboard)
- **Repo/Path**: `/` (Main Workspace)
- **Role**: Handles User Authentication, SSO, Global Progress Tracking, and Service Routing.
- **Tech Stack**: Next.js 16 (App Router), TypeScript, FastAPI (Backend), SQLite.
- **Port**: Frontend 3400, Backend 8000

### The Modules (Integrated Services)
Modules are separate applications (often with their own backends) embedded into the Shell via the `ServiceFrame` component.

1. **Writing Hub (AI Writer)**:
   - News-based writing platform
   - Integrated from `microservices/sugarclass-aiwriter`
   - Frontend: Next.js (Port 3401)
   - Backend: FastAPI + PostgreSQL (Port 8001)
   - Features: News collection, AI writing prompts, essay practice

2. **AI Teacher (Tutor)**:
   - RAG-based tutoring system
   - Integrated from `microservices/sugarclass-aitutor`
   - Frontend: React/Vite (Port 3402)
   - Backend: FastAPI + PostgreSQL (Port 8002)
   - Infrastructure: Qdrant (vector DB), Redis (caching)
   - Features: Syllabus-specific Q&A, mastery tracking, quiz generation, automatic content sync

3. **Quiz Master (Examiner)**:
   - AI-powered exam preparation platform
   - Integrated from `microservices/sugarclass-aiexaminer`
   - Frontend: Next.js (Port 3403)
   - Backend: FastAPI + SQLite (Port 8003)
   - Features: Material upload, folder organization, AI question generation (MCQ/Short Answer), question editing, progress tracking

4. **AI Materials**:
   - Content enrichment and exercise manager
   - Integrated from `microservices/sugarclass-aimaterials`
   - Backend: FastAPI + SQLite (Port 8004)
   - Frontend: React/Vite (Port 3404)
   - Features: Content enhancement with AI-generated images, exercise CRUD, content regeneration with customizable parameters, admin panel

---

## 3. Communication & Authentication Handshake
To maintain SSO across iframes without complex cross-domain cookies:
1. **Shell Side**: Stores the `token` in `localStorage`.
2. **SessionHandler**: A high-level component that periodically "pings" the child iframes with the current user token using `postMessage`.
3. **Child Side**: Listens for the `postMessage`, validates the token, and stores it in its own local context (e.g., `localStorage.setItem('sugarclass_token', ...)`) to authorize API requests to its own specialized backend.

---

## 4. Technical Stack Details

### Frontend (Main Dashboard)
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Vanilla CSS Modules (Global styles in `src/app/globals.css`).
- **Icons**: Lucide React.
- **Animations**: Framer Motion.
- **Key Components**:
    - `Sidebar`: Dynamic navigation with kid-friendly labels.
    - `ServiceFrame`: Handles iframe scaling, loading states, and token handshake.
    - `StatsCard`: Standardized metric visualization.

### Backend (Main Dashboard)
- **Framework**: FastAPI (Python 3.11+)
- **Auth**: JWT-based OAuth2.
- **Database**: SQLAlchemy 2.0 (Async) with SQLite.
- **Core Endpoints**:
    - `/api/v1/auth`: Login, Register, User profile.
    - `/api/v1/progress`: Unified endpoint for modules to report student activity.

### Microservice Tech Stacks

**AI Writer**:
- Frontend: Next.js with TypeScript
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Features: News scraping, AI-powered writing assistance

**AI Tutor**:
- Frontend: React with Vite
- Backend: FastAPI (Python)
- Databases: PostgreSQL (Content DB + Agent DB)
- Vector Store: Qdrant
- Cache: Redis
- Features: RAG-based tutoring, semantic search, session management

**AI Examiner**:
- Frontend: Next.js with TypeScript
- Backend: FastAPI (Python)
- Database: SQLite
- Features: PDF/image upload, AI question generation, material management

**AI Materials**:
- Frontend: React with Vite
- Backend: FastAPI (Python)
- Database: SQLite (shared with AI Tutor)
- Features: Content enhancement, exercise generation, admin CRUD

---

## 5. Deployment & Infrastructure
The project is orchestrated via `docker-compose.yml` for local development.

### Service Ports
- **Dashboard Frontend**: `localhost:3400`
- **Dashboard Backend**: `localhost:8000`
- **AI Writer Frontend**: `localhost:3401/aiwriter`
- **AI Writer Backend**: `localhost:8001`
- **AI Tutor Frontend**: `localhost:3402/aitutor`
- **AI Tutor Backend**: `localhost:8002`
- **AI Examiner Frontend**: `localhost:3403/examiner`
- **AI Examiner Backend**: `localhost:8003`
- **AI Materials Backend**: `localhost:8004`
- **AI Materials Frontend**: `localhost:3404`
- **Qdrant Dashboard**: `localhost:6333/dashboard`

### Network
- All containers communicate over a shared `sugarclass-network`.
- Database isolation: Each microservice has its own database (except AI Materials shares with AI Tutor).

---

## 6. Development Guidelines for AI Tools

### Building for Kids (Tone & Language)
- **Avoid**: "Institutional Grade", "Deployment", "Neural Synthesis", "Verification Stream".
- **Use**: "Smart Learning", "Ready to Go!", "My Progress", "Activity Feed".
- **Tone**: Professional yet encouraging. No placeholders (e.g., "Lorem Ipsum"). Use high-quality AI-generated content or real data.

### Styling Standards
- **Containers**: Use `.premium-card` class for consistent shadow, border-radius (`24px`), and glassmorphism.
- **Colors**:
    - Background: `#fdfbf7` (Ivory)
    - Primary: `#2c3e50` (Slate)
    - Accent: `#8e7d6b` (Bronze)
    - Success: `#4a5d4e` (Sage)
- **Alignment**:
    - Dashboards must use `align-items: stretch` to ensure uniform box heights.
    - Page contents should be left-aligned with a generous right-side margin (`120px` padding-right) for a modern, expansive feel.

### Dashboard Grid
The main dashboard uses a **1:1:1 Balanced Grid**. Every column weight should be equal to ensure symmetry and order.

---

## 7. Current Project State

### Fully Implemented Services
- **Auth**: Complete JWT-based authentication (Login/Register)
- **Dashboard**: Production-ready UI with real telemetry data
- **AI Writer**: Production-ready with active news fetching and writing assistance
- **AI Tutor**: Full RAG system with frontend, vector search, and automatic content synchronization
- **AI Examiner**: Complete exam preparation platform with material management and question editing
- **AI Materials**: Full content management system with AI enhancement and exercise generation

### Recent Features (2026-02)

**AI Examiner Teacher Customization**:
- Material management with folder organization
- Complete question editing (CRUD operations)
- Folder management (create, rename, add files, delete)
- Auto-naming from material filenames
- Student progress tracking

**AI Materials Content Management**:
- Content edit modal for HTML content, summary, and key terms
- Content regeneration modal with AI customization options (focus, temperature, sections)
- Content browser component with tree view navigation
- Backend CRUD API for content management
- LLM-powered content regeneration with background tasks

**AI Tutor Enhancements**:
- Full frontend interface with React/Vite
- Data sync agent for automatic content updates
- Enhanced RAG capabilities with Qdrant integration
- Session management with Redis caching

---

## 8. Integration Protocol
To add a new module:
1. Create a `microservices/service-name` directory with its own stack.
2. Add a route in the Shell at `frontend/src/app/(dashboard)/services/service-name/page.tsx`.
3. Use `<ServiceFrame name="..." serviceUrl="..." />`.
4. Ensure the child app's `lib/api.ts` (or equivalent) checks for `sugarclass_token` via `postMessage`.
5. Report activity back to the Shell using the `/api/v1/progress/` endpoint.
6. Add service configuration to `docker-compose.yml` with appropriate ports and networking.

---

## 9. Database Architecture

### Main Dashboard
- **Type**: SQLite
- **ORM**: SQLAlchemy 2.0 (Async)
- **Tables**: users, sessions, progress_logs

### AI Writer
- **Type**: PostgreSQL
- **Tables**: news_articles, drafts, writing_sessions

### AI Tutor
- **Type**: PostgreSQL (2 databases)
- **Content DB**: syllabuses, subjects, topics, subtopics, content_raw, content_processed
- **Agent DB**: sessions, messages, mastery_tracking
- **Vector Store**: Qdrant for semantic search

### AI Examiner
- **Type**: SQLite
- **Tables**: materials, quizzes, questions, sessions, progress

### AI Materials
- **Type**: SQLite (shared with AI Tutor)
- **Tables**: Uses same schema as AI Tutor Content DB
- **Additional**: exercises, questions tables for practice content

---

## 10. API Integration Points

### Shell → Modules
- Authentication token via `postMessage`
- User profile data
- Session management

### Modules → Shell
- Progress updates via `/api/v1/progress`
- Activity logging
- User metrics

### Inter-Module Communication
- AI Materials ↔ AI Tutor: Shared database for content
- All modules: Independent but can share user context via Shell

---

*Last Updated: 2026-02-12*
