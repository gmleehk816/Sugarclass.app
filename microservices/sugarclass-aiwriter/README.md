# 🚀 NewsCollect AI Writer

Age-appropriate news & AI writing tool for students. Built with Next.js, FastAPI, and Google Gemini AI.

## ✨ Features

- **AI Writer**: Prewrite summaries, suggestions, and text improvement
- **News Aggregation**: Multiple sources with smart classification
- **Age-Appropriate**: Content for ages 7-10, 11-14, 15-18
- **Modern Stack**: Next.js + FastAPI + PostgreSQL + Docker

---

## 🚀 Quick Start (Local)

```bash
# Deploy locally
docker-compose up -d --build

# Access application
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
```

**Note:** `.env` file is already fully configured with all necessary values.

---

## 🚀 Deploy to VPS

### Step 1: Copy to VPS

```bash
# Copy entire project to VPS
scp -r . user@your-vps-ip:~/newscollect

# SSH into VPS
ssh user@your-vps-ip
```

### Step 2: Deploy

```bash
cd ~/newscollect
docker-compose up -d --build
```

That's it! Application is now running.

**See [DEPLOYMENT.md](DEPLOYMENT.md) for full details.**

---

## ⚙️ Environment Configuration

The `.env` file is **fully configured** and ready for both local and production:

**Already Set:**
- `POSTGRES_PASSWORD` - Database password
- `SECRET_KEY` - Application secret key
- `LLM_API_KEY` - Gemini API key (AI features)
- `LLM_BASE_URL` - API endpoint
- `LLM_MODEL` - Model configuration
- `CORS_ORIGINS` - Includes `sugarclass.app` and localhost

**Optional:**
- `NEWSAPI_KEY`, `GNEWS_API_KEY`, `NEWSCATCHER_API_KEY` - Add these to enable automatic news collection

**No changes needed!** The same `.env` file works for both environments.

---

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[docs/API.md](docs/API.md)** - API documentation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture

---

## 🏗️ Project Structure

```
newscollect/
├── backend/           # FastAPI backend
├── frontend/          # Next.js frontend
├── collector/         # News collection system
├── scripts/           # Deployment scripts
├── docs/              # Documentation
├── docker-compose.yml  # Docker orchestration
└── .env               # Environment variables (fully configured)
```

---

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update after code changes
docker-compose up -d --build
```

---

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/articles` | List articles |
| GET | `/articles/{id}` | Get single article |
| POST | `/ai/prewrite` | Generate summary |
| POST | `/ai/suggest` | Get suggestions |
| POST | `/ai/improve` | Improve text |

See [docs/API.md](docs/API.md) for full API documentation.

---

## 🌐 Access Points

**Local Development:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

**Production (VPS):**
- Frontend: `https://sugarclass.app/aiwriter`
- Backend API: Internal (proxied via nginx)

---

**Version**: 3.0.0 | **Status**: Production Ready ✅
