# Adding AI Examiner to Production Deployment Guide

**Purpose:** This guide explains how to safely add the AI Examiner microservice to your existing Sugarclass.app production deployment without disrupting the running services.

**Date:** January 26, 2026  
**Status:** ✅ Safe to Deploy

---

## Changes Made (Safe for Existing Services)

### ✅ Changes That Will NOT Affect Existing Services

These changes add new functionality without modifying existing service behavior:

#### 1. Gateway Health Check Endpoint
**File:** `gateway/nginx/nginx.conf`
**Change:** Added `/health` endpoint to nginx
**Impact:** None - This adds a new endpoint that Docker Compose was already expecting. It doesn't modify any existing routing or behavior.

```nginx
# Health check endpoint
location /health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

#### 2. Tutor Backend Health Check
**File:** `docker-compose.prod.yml`
**Change:** Added health check to `tutor-backend` service
**Impact:** None - This only adds monitoring to an existing service. It doesn't change how the service operates.

```yaml
healthcheck:
  test: [ "CMD-SHELL", "curl -f http://127.0.0.1:8000/health || exit 1" ]
  interval: 30s
  timeout: 10s
  retries: 3
```

#### 3. AI Examiner Services (New Addition)
**Files:** `docker-compose.prod.yml`, `gateway/nginx/nginx.conf`
**Change:** Added new AI Examiner backend and frontend services
**Impact:** None - These are entirely new services that don't interact with or modify existing services.

---

## Pre-Deployment Checklist

- [ ] Verify AI Examiner environment variables are set in `microservices/sugarclass-aiexaminer/.env`
- [ ] Ensure gateway nginx configuration is correct
- [ ] Test AI Examiner services locally first (optional but recommended)
- [ ] Backup current production configuration

---

## Deployment Steps

### Step 1: Verify Environment Variables

Ensure the AI Examiner has its required environment variables:

```bash
# Check if the file exists
ls -la microservices/sugarclass-aiexaminer/.env

# If needed, create it with required variables:
# DATABASE_URL=sqlite+aiosqlite:///./database/examiner.db
# SUGARCLASS_API_URL=https://sugarclass.app/api/v1
```

### Step 2: Deploy to VPS

The safest way to deploy is to pull the changes and build only the new services:

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Navigate to project directory
cd /var/www/Sugarclass.app

# Pull latest changes
git pull origin main

# Deploy ONLY the new AI Examiner services
docker compose -f docker-compose.prod.yml up -d --build aiexaminer-backend aiexaminer-frontend

# Or deploy everything (safe since existing services won't be modified)
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Verify AI Examiner Services

Check that the new services are running:

```bash
# Check all containers
docker compose -f docker-compose.prod.yml ps

# Check AI Examiner logs
docker compose -f docker-compose.prod.yml logs aiexaminer-backend
docker compose -f docker-compose.prod.yml logs aiexaminer-frontend

# Verify health status
docker compose -f docker-compose.prod.yml ps | grep aiexaminer
```

### Step 4: Test AI Examiner Functionality

Access the AI Examiner through your domain:

- **Frontend:** `https://sugarclass.app/examiner/`
- **API Health:** `https://sugarclass.app/examiner/api/v1/health`

Test key functionality:
1. Upload a PDF document
2. Generate a quiz
3. Take the quiz
4. Check progress tracking

### Step 5: Verify Existing Services Still Work

Ensure your existing services are unaffected:

- **Main Dashboard:** `https://sugarclass.app/`
- **AI Writer:** `https://sugarclass.app/aiwriter/`
- **AI Tutor:** `https://sugarclass.app/aitutor/`

---

## What If Something Goes Wrong?

### Scenario 1: AI Examiner Services Won't Start

```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs aiexaminer-backend
docker compose -f docker-compose.prod.yml logs aiexaminer-frontend

# Common issues:
# - Missing environment variables
# - Database initialization errors
# - Port conflicts (shouldn't happen with Docker networking)
```

### Scenario 2: Existing Services Affected

If existing services show issues, you can quickly revert:

```bash
# Stop AI Examiner services only
docker compose -f docker-compose.prod.yml stop aiexaminer-backend aiexaminer-frontend

# Or revert to previous commit
git log --oneline -10  # Find the previous commit hash
git checkout <previous-commit-hash>
docker compose -f docker-compose.prod.yml up -d
```

### Scenario 3: Gateway Issues

If the gateway has problems:

```bash
# Check nginx configuration
docker compose -f docker-compose.prod.yml logs gateway

# Restart gateway
docker compose -f docker-compose.prod.yml restart gateway
```

---

## Monitoring AI Examiner

After deployment, monitor the new services:

```bash
# Real-time logs
docker compose -f docker-compose.prod.yml logs -f aiexaminer-backend

# Resource usage
docker stats aiexaminer-backend aiexaminer-frontend

# Health status
docker compose -f docker-compose.prod.yml ps
```

---

## Rollback Plan

If you need to completely remove AI Examiner:

```bash
# Stop and remove AI Examiner services
docker compose -f docker-compose.prod.yml stop aiexaminer-backend aiexaminer-frontend
docker compose -f docker-compose.prod.yml rm -f aiexaminer-backend aiexaminer-frontend

# Remove volumes (this will delete all AI Examiner data!)
docker compose -f docker-compose.prod.yml down -v

# Note: Be careful with -v flag as it removes volumes
```

---

## Summary

### What's Being Added:
- ✅ AI Examiner Backend (FastAPI, SQLite database)
- ✅ AI Examiner Frontend (Next.js)
- ✅ Gateway routing for `/examiner/` paths
- ✅ Health check endpoint for gateway
- ✅ Health monitoring for tutor backend

### What's NOT Changing:
- ✅ Main Dashboard (frontend/backend) - No changes
- ✅ AI Writer (frontend/backend) - No changes
- ✅ AI Tutor (frontend/backend) - No changes to behavior, only added monitoring
- ✅ All existing databases - No changes
- ✅ All existing configurations - No breaking changes

### Safety Guarantees:
1. **Docker Compose** will only rebuild changed services
2. **Existing containers** will continue running unless explicitly restarted
3. **Network isolation** ensures new services can't affect existing ones
4. **Rollback is simple** - just stop the new services

### Risk Level: **VERY LOW** 🟢

The deployment adds entirely new services without modifying existing ones. The only changes to existing services are:
- Gateway: Adds a health check endpoint (non-breaking)
- Tutor Backend: Adds health monitoring (non-breaking)

---

## Post-Deployment Tasks

After successful deployment:

1. **Set up backups for AI Examiner data**
   ```bash
   # Backup the database and uploads
   docker compose -f docker-compose.prod.yml exec aiexaminer-backend \
     tar -czf /tmp/examiner-backup.tar.gz /app/database /app/uploads
   docker cp aiexaminer-backend:/tmp/examiner-backup.tar.gz ./backups/
   ```

2. **Monitor resource usage**
   - AI Examiner may have higher memory usage during PDF processing
   - Consider VPS resource allocation if you see performance issues

3. **Document the new service**
   - Update any internal documentation
   - Train users on the new AI Examiner functionality

---

**Questions?** If you encounter any issues during deployment, check the logs and refer to the troubleshooting section above.