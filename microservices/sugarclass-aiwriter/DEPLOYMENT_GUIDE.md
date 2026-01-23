# 🚀 Complete Deployment Guide - NewsCollect AI Writer

## 📌 Deployment Overview

This application will be deployed as a **sub-path** under an existing domain:
- **Main Domain**: `https://sugarclass.app`
- **AI Writer Path**: `https://sugarclass.app/aiwriter`
- **API Path**: `https://sugarclass.app/aiwriter/api`

### 📍 VPS Information
- **VPS IP**: 156.238.242.71
- **SSH User**: root
- **Project Directory**: /var/www/sugarclass-aiwriter

### 🔗 GitHub Repository
- **Repository**: https://github.com/gmleehk816/sugarclass-aiwriter.git
- **Branch**: master

---

## ✨ Quick Deployment (Recommended)

### Option 1: Automated VPS Deployment (Easiest - 1-Click)

This is the fastest way to deploy - the script handles everything automatically!

```bash
# From your local project directory
cd c:/Users/gmhome/SynologyDrive/coding/realtimewriter/newscollect

# Make sure .env file exists in current directory
# Run the automated deployment script
bash scripts/deploy_to_vps.sh
```

**What the script does:**
- ✅ Checks for local .env file
- ✅ Tests SSH connection to VPS
- ✅ Backs up existing deployment and database
- ✅ Transfers files to /var/www/sugarclass-aiwriter
- ✅ Uploads your .env file to VPS
- ✅ Installs Docker and Docker Compose (if needed)
- ✅ Installs Nginx and Certbot (if needed)
- ✅ Builds and starts all containers
- ✅ Configures Nginx for sub-path deployment
- ✅ Sets up SSL certificates automatically (uses existing cert for sugarclass.app)
- ✅ Populates database if empty (0 articles)
- ✅ Performs health checks
- ✅ Provides final verification and URLs

**Prerequisites:**
1. Have `.env` file in your project root with all required configurations
2. Ensure VPS (156.238.242.71) is accessible via SSH as root user
3. Domain DNS (sugarclass.app) points to VPS IP
4. Run script from project root directory

**No post-deployment steps needed!** The script handles everything including:
- Nginx configuration
- SSL certificate setup
- Database population
- Health verification

### Option 2: Deploy from GitHub on VPS (Recommended)

If you prefer to deploy directly from GitHub on the VPS:

```bash
# Step 1: SSH into VPS
ssh root@156.238.242.71

# Step 2: Install git (if not installed)
apt update && apt install -y git

# Step 3: Clone the repository
cd /var/www
git clone https://github.com/gmleehk816/sugarclass-aiwriter.git
cd sugarclass-aiwriter

# Step 4: Create .env file (see Environment Configuration section below)
nano .env

# Step 5: Make deployment script executable
chmod +x scripts/deploy_on_vps.sh

# Step 6: Run deployment script
bash scripts/deploy_on_vps.sh
```

**What the script does:**
- ✅ Checks for .env file in project directory
- ✅ Backs up existing deployment and database
- ✅ Installs Docker and Docker Compose (if needed)
- ✅ Installs Nginx and Certbot (if needed)
- ✅ Builds and starts all containers
- ✅ Configures Nginx for sub-path deployment
- ✅ Sets up SSL certificates automatically (uses existing cert for sugarclass.app)
- ✅ Populates database if empty (0 articles)
- ✅ Performs health checks
- ✅ Provides final verification and URLs

**Updating from GitHub:**

```bash
# SSH into VPS
ssh root@156.238.242.71

# Pull latest changes
cd /var/www/sugarclass-aiwriter
git pull origin master

# Redeploy (this will rebuild and restart services)
bash scripts/deploy_on_vps.sh
```

**Note**: This is the recommended approach for production as it:
- Ensures you're always deploying the latest code from GitHub
- Allows easy rollback if needed (git revert)
- Provides better version control
- Can be automated with CI/CD pipelines

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure:

- [ ] GitHub repository is accessible: https://github.com/gmleehk816/sugarclass-aiwriter.git
- [ ] VPS (156.238.242.71) is accessible via SSH as root
- [ ] You have Gemini API key ready (required for AI features)
- [ ] Domain DNS (sugarclass.app) points to VPS IP: 156.238.242.71
- [ ] VPS has at least 2GB RAM and 20GB disk space

---

## 🔧 Environment Configuration

### Create `.env` File

Create a `.env` file in the project root with the following configuration:

```bash
# =============================================================================
# NEWSCOLLECT CONFIGURATION
# Same configuration for both local and production deployment
# =============================================================================

# =============================================================================
# DATABASE
# =============================================================================
POSTGRES_PASSWORD=NewsCollect2024!Secure
POSTGRES_DB=newscollect
POSTGRES_USER=postgres

# =============================================================================
# BACKEND API
# =============================================================================
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# =============================================================================
# FRONTEND
# =============================================================================
NEXT_PUBLIC_API_URL=https://sugarclass.app/aiwriter/api

# =============================================================================
# GEMINI AI CONFIGURATION
# =============================================================================
LLM_BASE_URL=https://hb.dockerspeeds.asia/
LLM_API_KEY=sk-UDVPC6AcYWjDF8S1t4ujs75dmNoVddhnsT3AL3m10NF9kOTm
LLM_MODEL=gemini-3-flash-preview
LLM_MODEL_SUMMARY=gemini-3-flash-preview
LLM_MODEL_DRAFT=gemini-3-flash-preview

# =============================================================================
# NEWS API KEYS (Optional - for automatic news collection)
# Leave empty if not using the collector. Add your keys below to enable news collection.
# =============================================================================
NEWSAPI_KEY=
GNEWS_API_KEY=
NEWSCATCHER_API_KEY=

# =============================================================================
# COLLECTION SCHEDULER
# =============================================================================
ENABLE_SCHEDULER=true
SCHEDULER_TIMEZONE=UTC

# =============================================================================
# COLLECTION LIMITS
# =============================================================================
RATE_LIMIT_DELAY=1.0
MAX_ARTICLES_PER_SOURCE=50
ARTICLES_RETENTION_DAYS=30

# =============================================================================
# SECURITY & CORS
# =============================================================================
SECRET_KEY=NewsCollect2024!SecretKeyHere
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,https://sugarclass.app,https://www.sugarclass.app

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO
```

### Critical Variables

**Already Configured:**
- `POSTGRES_PASSWORD` - Set to: NewsCollect2024!Secure
- `SECRET_KEY` - Set to: NewsCollect2024!SecretKeyHere
- `LLM_API_KEY` - Configured with custom endpoint
- `LLM_BASE_URL` - Set to: https://hb.dockerspeeds.asia/
- `LLM_MODEL` - Set to: gemini-3-flash-preview

**Optional Variables:**
- `NEWSAPI_KEY`, `GNEWS_API_KEY`, `NEWSCATCHER_API_KEY` - For more news sources (leave empty if not needed)

---

## 🚀 Manual Deployment Steps

If you prefer to deploy manually instead of using the automated script:

### Step 1: Transfer Files to VPS

```bash
# From your local machine
cd c:/Users/gmhome/SynologyDrive/coding/realtimewriter/newscollect

# Upload files to VPS
scp -r . root@156.238.242.71:/var/www/sugarclass-aiwriter
```

Or use rsync (better for large files):
```bash
rsync -avz --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  --exclude='.git' \
  ./ root@156.238.242.71:/var/www/sugarclass-aiwriter/
```

### Step 2: SSH into VPS

```bash
ssh root@156.238.242.71
cd /var/www/sugarclass-aiwriter
```

### Step 3: Install Docker (if not installed)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### Step 4: Create .env File

```bash
nano .env
```

Paste the configuration from the "Environment Configuration" section above.

### Step 5: Deploy Containers

```bash
# Stop any existing containers
docker-compose down

# Build and start containers
docker-compose up -d --build

# Wait for services to start (10-15 seconds)
sleep 15

# Check container status
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
newscollect_backend     Up (healthy)        0.0.0.0:8000->8000/tcp
newscollect_db          Up (healthy)        5432/tcp
newscollect_frontend     Up                  0.0.0.0:3000->3000/tcp
```

### Step 6: Configure Nginx

The nginx configuration file (`nginx/aiwriter.conf`) is now a **complete server block** that includes:
- HTTP server with auto-redirect to HTTPS
- HTTPS server with SSL certificates
- All location blocks for /aiwriter sub-path
- Security headers and SSL optimization

```bash
# Copy Nginx configuration
sudo cp nginx/aiwriter.conf /etc/nginx/sites-available/sugarclass-app

# Enable the site
sudo ln -sf /etc/nginx/sites-available/sugarclass-app /etc/nginx/sites-enabled/

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Note**: The nginx configuration automatically:
- Redirects HTTP to HTTPS
- Uses SSL certificates from Let's Encrypt (will be obtained in next step)
- Configures /aiwriter for frontend and /aiwriter/api for backend
- Sets up security headers and SSL best practices

### Step 7: Setup SSL Certificate

**Important SSL Certificate Information:**

Your existing SSL certificate for `sugarclass.app` automatically covers the `/aiwriter` sub-path. **No separate certificate is needed for /aiwriter**.

A single SSL certificate for `sugarclass.app` works for:
- `https://sugarclass.app` (root domain)
- `https://www.sugarclass.app` (www subdomain)
- `https://sugarclass.app/aiwriter` (sub-path)
- `https://sugarclass.app/aiwriter/api` (API endpoints)
- Any other sub-paths under the domain

**If you need to obtain or renew a certificate:**

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate (if not already exists)
sudo certbot --nginx -d sugarclass.app -d www.sugarclass.app

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (option 2)

# Verify certificate
sudo certbot certificates

# Renew certificate (if needed)
sudo certbot renew

# Force renewal (if certificate is expired)
sudo certbot renew --force-renewal
```

**Certificate Auto-Renewal:**

Certbot automatically sets up auto-renewal via cron. To verify:

```bash
# Check certbot timer
systemctl list-timers | grep certbot

# Manually test renewal (dry-run)
sudo certbot renew --dry-run
```

**No additional certificate commands are needed for /aiwriter!**

### Step 8: Verify Deployment

```bash
# Test backend health
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/api/articles
curl http://localhost:8000/api/stats

# Check logs
docker-compose logs -f --tail=50
```

---

## 📊 Database Setup

### Initial Database Population

The database starts empty. Populate it with news articles:

```bash
# SSH into VPS
ssh root@156.238.242.71
cd /var/www/sugarclass-aiwriter

# Run the database population script
docker-compose exec backend python /app/populate_db.py
```

This will:
- Fetch articles from RSS feeds (BBC, CNN, etc.)
- Extract full article text
- Store in database
- Report statistics

**Expected output:**
```
============================================================
NewsCollect - Database Population Script
============================================================

Current database status:
  Total articles: 0
  Full articles: 0

Starting collection from RSS sources...
------------------------------------------------------------

[Collect] Starting collection from bbc.com...
[Collect] Stored: Leaked photos show hundreds killed... (newspaper4k)
[Collect] Completed bbc.com: 20 articles stored

[Collect] Starting collection from cnn.com...
[Collect] Completed cnn.com: 20 articles stored

Collection complete!

Articles stored: 40
```

### Manual Article Collection

You can also collect specific articles:

```bash
# Collect from all sources
docker-compose exec backend python -c "from collector.collector import collect_all; collect_all(limit_per_source=20)"

# Collect from a single URL
docker-compose exec backend python -c "from collector.collector import collect_single_article; collect_single_article('https://example.com/article')"

# Collect from specific API
docker-compose exec backend python -c "from collector.collector import collect_from_api; collect_from_api('newsapi', query='technology', limit=10)"
```

---

## 🔍 Verification

### Test from VPS

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"NewsCollect API","version":"1.0"}

# Get articles
curl http://localhost:8000/api/articles

# Get stats
curl http://localhost:8000/api/stats

# Frontend
curl -I http://localhost:3000
```

### Test from Public Internet

Open these URLs in your browser:

- **Frontend**: https://sugarclass.app/aiwriter
- **API Health**: https://sugarclass.app/aiwriter/health
- **API Docs**: https://sugarclass.app/aiwriter/api/docs
- **Articles**: https://sugarclass.app/aiwriter/api/articles
- **Stats**: https://sugarclass.app/aiwriter/api/stats

### Expected Results

✅ Frontend loads and shows article list
✅ Can click on articles to view details
✅ AI features work (prewrite, suggestions)
✅ API documentation is accessible
✅ No console errors in browser

---

## 🛠️ Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
docker-compose restart frontend
```

### Stop/Start

```bash
# Stop all
docker-compose down

# Start all
docker-compose up -d

# Rebuild after changes
docker-compose down
docker-compose up -d --build
```

### Database Operations

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres newscollect > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres newscollect < backup.sql

# Access database shell
docker-compose exec postgres psql -U postgres newscollect

# Check article count
docker-compose exec backend python -c "from database import get_stats; print(get_stats())"
```

### Update Deployment

```bash
# SSH into VPS
ssh root@156.238.242.71
cd /var/www/sugarclass-aiwriter

# Pull latest changes from GitHub
git pull origin master

# Or upload new files manually, then:
docker-compose down
docker-compose up -d --build

# Watch logs during startup
docker-compose logs -f
```

---

## 🐛 Troubleshooting

### Issue: Frontend Shows "No Articles Found"

**Cause**: Database is empty

**Solution**:
```bash
docker-compose exec backend python /app/populate_db.py
```

### Issue: "Network Error" When Connecting to API

**Cause**: Frontend can't reach backend

**Solutions**:

1. Check `.env` file on VPS:
```bash
cat .env | grep NEXT_PUBLIC_API_URL
# Should be: NEXT_PUBLIC_API_URL=https://sugarclass.app/aiwriter/api
```

2. Verify backend is running:
```bash
docker-compose ps backend
curl http://localhost:8000/health
```

3. Check Nginx configuration:
```bash
sudo nginx -t
sudo systemctl status nginx
```

### Issue: AI Features Not Working

**Cause**: Missing or invalid Gemini API key

**Solution**:
```bash
# Check API key
cat .env | grep LLM_API_KEY

# Update with valid key
nano .env

# Restart backend
docker-compose restart backend

# Check logs
docker-compose logs backend | grep -i gemini
```

### Issue: Container Keeps Restarting

**Cause**: Configuration error or dependency issue

**Solution**:
```bash
# Check logs
docker-compose logs backend

# Check configuration
docker-compose config

# Recreate containers
docker-compose down
docker-compose up -d --force-recreate
```

### Issue: 502 Bad Gateway

**Cause**: Backend not responding

**Solution**:
```bash
# Check if backend is running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Test backend directly
curl http://localhost:8000/health

# Restart backend
docker-compose restart backend
```

### Issue: SSL Certificate Errors

**Cause**: Certificate expired or misconfigured

**Solution**:
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Reload Nginx
sudo systemctl reload nginx
```

### Issue: Database Connection Failed

**Cause**: PostgreSQL not running or wrong credentials

**Solution**:
```bash
# Check PostgreSQL container
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres

# Check environment variables
docker-compose exec backend env | grep POSTGRES

# Restart services
docker-compose restart backend postgres
```

### Issue: Can't Connect to VPS

**Cause**: SSH access blocked or credentials wrong

**Solution**:

1. Verify VPS IP is correct:
```bash
ping 156.238.242.71
```

2. Check SSH is running on VPS:
```bash
# From another terminal
nmap -p 22 156.238.242.71
```

3. Check firewall rules:
```bash
# On VPS
ufw status
ufw allow 22/tcp
```

4. Try verbose SSH:
```bash
ssh -vvv root@156.238.242.71
```

---

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl -I http://localhost:3000

# Database
docker-compose exec postgres pg_isready -U postgres
```

### Resource Usage

```bash
# Docker stats
docker stats

# Disk usage
df -h

# Memory usage
free -h

# CPU usage
top
```

### Log Monitoring

```bash
# Follow all logs
docker-compose logs -f

# Search for errors
docker-compose logs | grep -i error
docker-compose logs | grep -i exception

# Count errors
docker-compose logs | grep -i error | wc -l
```

---

## 🔒 Security Best Practices

1. **Strong Passwords**: Use strong passwords for PostgreSQL
2. **API Keys**: Never commit API keys to git
3. **SSL Certificates**: Ensure SSL is enabled and auto-renewing
4. **Firewall**: Only expose necessary ports (80, 443)
5. **Regular Updates**: Keep system and Docker updated
6. **Backups**: Set up automated database backups

### Automated Database Backup

```bash
# Create backup script
cat > /var/www/sugarclass-aiwriter/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/sugarclass-aiwriter"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U postgres newscollect > $BACKUP_DIR/newscollect_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "newscollect_*.sql" -mtime +7 -delete

echo "Backup completed: newscollect_$DATE.sql"
EOF

chmod +x /var/www/sugarclass-aiwriter/scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line: 0 2 * * * /var/www/sugarclass-aiwriter/scripts/backup.sh
```

---

## 📝 Environment Variables Reference

### Required Variables
- `POSTGRES_PASSWORD` - PostgreSQL password
- `SECRET_KEY` - Application secret key
- `LLM_API_KEY` - Gemini AI API key (required for AI features)

### Optional but Recommended
- `NEXT_PUBLIC_API_URL` - Frontend API URL (set to production URL)
- `CORS_ORIGINS` - Allowed CORS origins
- `NEWSAPI_KEY`, `GNEWS_API_KEY`, `NEWSCATCHER_API_KEY` - Additional news sources

### Advanced Configuration
- `ENABLE_SCHEDULER` - Enable automatic news collection
- `SCHEDULER_TIMEZONE` - Scheduler timezone
- `MAX_ARTICLES_PER_SOURCE` - Limit articles per source
- `RATE_LIMIT_DELAY` - Rate limiting delay (seconds)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

---

## 🎯 Success Checklist

Your deployment is successful when:

- [ ] All 3 containers are running (backend, frontend, postgres)
- [ ] All containers show "healthy" status
- [ ] Backend health endpoint returns 200 OK
- [ ] Frontend loads at https://sugarclass.app/aiwriter
- [ ] API docs accessible at https://sugarclass.app/aiwriter/api/docs
- [ ] Can fetch articles from API
- [ ] Database has articles (check /api/stats)
- [ ] AI features work (prewrite, suggestions)
- [ ] SSL certificate valid (green lock)
- [ ] No errors in logs
- [ ] Can manually collect new articles

---

## 🚀 Quick Reference

### Deployment Commands

```bash
# Deploy (automated)
bash scripts/deploy_to_vps.sh

# SSH into VPS
ssh root@156.238.242.71

# View project
cd /var/www/sugarclass-aiwriter

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Populate database
docker-compose exec backend python /app/populate_db.py

# Backup database
docker-compose exec postgres pg_dump -U postgres newscollect > backup.sql
```

### URLs

- **Frontend**: https://sugarclass.app/aiwriter
- **API Health**: https://sugarclass.app/aiwriter/health
- **API Docs**: https://sugarclass.app/aiwriter/api/docs
- **Articles**: https://sugarclass.app/aiwriter/api/articles
- **Stats**: https://sugarclass.app/aiwriter/api/stats

### Repository

- **GitHub**: https://github.com/gmleehk816/sugarclass-aiwriter.git
- **VPS IP**: 156.238.242.71
- **VPS User**: root

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs -f`
2. **Verify configuration**: `docker-compose config`
3. **Test locally**: Run `docker-compose up` on your local machine
4. **Check VPS resources**: CPU, memory, disk space
5. **Verify DNS**: Ensure sugarclass.app points to 156.238.242.71

---

**Deployment complete! 🎉**

Your NewsCollect AI Writer is now running at: https://sugarclass.app/aiwriter
