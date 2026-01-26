# Project Context: Sugarclass AI Learning Orchestrator

## 1. Overview
**Sugarclass** is a premium, institutional-grade learning orchestrator designed for kids and young students. It serves as a "Mission Control" hub that integrates multiple specialized AI tools into a unified, secure, and engaging environment.

- **Primary Goal**: To provide a safe, smart, and beautiful workspace where students can read news, write stories, ask AI teachers for help, and test their knowledge.
- **Target Audience**: Students ages 7-18, teachers, and educational institutions.
- **Design Aesthetic**: "Slate & Ivory" – A clean, high-end professional look that feels like an "Enterprise for Kids" platform. High use of glassmorphism, fluid animations (Framer Motion), and premium iconography (Lucide).

---

## 2. Core Architecture: "Shell & Module"
The application is built using a **Micro-Frontend/Service Architecture** integrated via a secure Iframe Shell.

### The Shell (Dashboard)
- **Repo/Path**: `/` (Main Workspace)
- **Role**: Handles User Authentication, SSO, Global Progress Tracking, and Service Routing.
- **Tech Stack**: Next.js 16 (App Router), TypeScript, FastAPI (Backend), SQLite.

### The Modules (Integrated Services)
Modules are separate applications (often with their own backends) embedded into the Shell via the `ServiceFrame` component.
1. **Writing Hub (AI Writer)**: A news-based writing platform. Integrated from `../sugarclass-aiwriter`.
2. **AI Teacher (Tutor)**: Placeholder for conceptual synthesis and tutoring.
3. **Quiz Master (Examiner)**: Integrated from `../sugarclass-aiexaminer`.

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
- **Database**: SQLAlchemy 2.0 (Async).
- **Core Endpoints**:
    - `/api/v1/auth`: Login, Register, User profile.
    - `/api/v1/progress`: Unified endpoint for modules to report student activity.

---

## 5. Deployment & Infrastructure
The project is orchestrated via `docker-compose.yml` for local development.

- **Dashboard (Shell)**: `localhost:3000` (Backend: `localhost:8000`)
- **AI Writer (Module)**: `localhost:3001/aiwriter` (Backend: `localhost:8001`)
- **Network**: All containers communicate over a shared `sugarclass-network`.

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
- **Auth**: Fully implemented (Login/Register).
- **Dashboard**: UI established with real telemetry data.
- **AI Writer**: Production-ready, news-fetching active, integrated via port 3001.
- **AI Teacher/Quiz Master**: UI Placeholders in the sidebar/dashboard; core logic and frame urls need implementation.

---

## 8. Integration Protocol
To add a new module:
1. Create a `../service-name` directory with its own stack.
2. Add a route in the Shell at `src/app/(dashboard)/services/service-name/page.tsx`.
3. Use `<ServiceFrame name="..." serviceUrl="..." />`.
4. Ensure the child app's `lib/api.ts` (or equivalent) checks for `sugarclass_token`.
5. Report activity back to the Shell using the `/progress/` endpoint.
