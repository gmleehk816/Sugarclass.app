#!/bin/bash

# NewsCollect AI Writer - VPS Deployment Script
# 1-Click Deployment to sugarclass-aiwriter on VPS 156.238.242.71

set -e  # Exit immediately on ANY error

echo "🚀 NewsCollect AI Writer - 1-Click VPS Deployment"
echo "=================================================="
echo ""

# Configuration
REMOTE_USER="root"
REMOTE_HOST="156.238.242.71"
REMOTE_DIR="/var/www/sugarclass-aiwriter"
# Convert Windows path to bash-compatible path for Git Bash/WSL
LOCAL_ENV_FILE="/c/Users/gmhome/SynologyDrive/coding/realtimewriter/newscollect/.env"

echo "📍 Target VPS: ${REMOTE_USER}@${REMOTE_HOST}"
echo "📂 Remote Directory: ${REMOTE_DIR}"
echo ""

# Check if .env file exists locally
if [ ! -f "${LOCAL_ENV_FILE}" ]; then
    echo "❌ ERROR: .env file not found in current directory!"
    echo "   Please create .env file with your configuration before deploying."
    exit 1
fi
echo "✅ Found .env file locally"
echo ""

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH connection successful'" > /dev/null 2>&1; then
    echo "❌ ERROR: Cannot connect to VPS!"
    echo "   Please check:"
    echo "   1. VPS is running at ${REMOTE_HOST}"
    echo "   2. SSH key is configured"
    echo "   3. SSH access is enabled"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Create /var/www directory if it doesn't exist
echo "📁 Ensuring /var/www directory exists..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p /var/www"

# Backup existing deployment if it exists
echo "📦 Checking for existing deployment..."
if ssh ${REMOTE_USER}@${REMOTE_HOST} "[ -d ${REMOTE_DIR} ]"; then
    BACKUP_DIR="${REMOTE_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up existing deployment to ${BACKUP_DIR}..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "cp -r ${REMOTE_DIR} ${BACKUP_DIR}"
    echo "✅ Backup created"
    
    # Backup database if containers are running
    echo "💾 Backing up database..."
    if ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose ps postgres 2>/dev/null | grep -q Up"; then
        ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd /var/www/sugarclass-aiwriter
docker-compose exec -T postgres pg_dump -U postgres newscollect > backup.sql
echo "✅ Database backed up"
ENDSSH
    else
        echo "ℹ️  No existing database to backup"
    fi
else
    echo "ℹ️  No existing deployment found"
fi
echo ""

# Create remote directory with proper permissions
echo "📁 Creating remote directory with proper permissions..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR} && chmod 755 ${REMOTE_DIR}"

# Copy files to VPS using rsync with exclusions
echo "📤 Copying files to VPS..."
echo "   Excluding: node_modules, .next, .git, __pycache__..."
rsync -avz --progress \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    --exclude='backup.sql' \
    --exclude='__pycache__/' \
    --exclude='node_modules/' \
    --exclude='.next/' \
    ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

echo "✅ Files copied successfully"
echo ""

# Copy .env file separately (ensure it's uploaded)
echo "📤 Uploading .env file..."
scp ${LOCAL_ENV_FILE} ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/.env
echo "✅ .env file uploaded"
echo ""

# Setup VPS environment and deploy
echo "🔧 Setting up VPS environment..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd /var/www/sugarclass-aiwriter

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    apt update
    apt install -y nginx
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing Certbot..."
    apt install -y certbot python3-certbot-nginx
fi

echo "✅ VPS environment ready"
ENDSSH
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose down 2>/dev/null || true"
echo "✅ Containers stopped"
echo ""

# Build and start containers
echo "🔨 Building containers..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose build"

echo "🚀 Starting services..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose up -d"

echo "⏳ Waiting for services to start (30 seconds)..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "sleep 30"

echo "✅ Services started"
echo ""

# Configure Nginx
echo "🔧 Configuring Nginx..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
# Copy Nginx configuration
cp /var/www/sugarclass-aiwriter/nginx/aiwriter.conf /etc/nginx/sites-available/sugarclass-app

# Enable the site
ln -sf /etc/nginx/sites-available/sugarclass-app /etc/nginx/sites-enabled/

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ ERROR: Nginx configuration test failed!"
    nginx -t
    exit 1
fi

# Reload Nginx
systemctl reload nginx
echo "✅ Nginx reloaded"
ENDSSH
echo ""

# Setup SSL certificate
echo "🔐 Setting up SSL certificate..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
# Check if certificate already exists for sugarclass.app
if certbot certificates 2>/dev/null | grep -q "sugarclass.app"; then
    echo "ℹ️  SSL certificate already exists for sugarclass.app"
    echo "ℹ️  This certificate covers /aiwriter sub-path automatically"
else
    echo "📜 Obtaining SSL certificate for sugarclass.app..."
    # Non-interactive certbot setup
    certbot --nginx -d sugarclass.app -d www.sugarclass.app \
        --non-interactive \
        --agree-tos \
        --email admin@sugarclass.app \
        --redirect \
        --force-renewal
    
    if certbot certificates 2>/dev/null | grep -q "sugarclass.app"; then
        echo "✅ SSL certificate obtained successfully"
        echo "ℹ️  This certificate covers both root domain and /aiwriter sub-path"
    else
        echo "⚠️  Warning: SSL certificate setup failed"
        echo "   Please run: sudo certbot --nginx -d sugarclass.app"
    fi
fi
ENDSSH
echo ""

# Health checks
echo "🔍 Performing health checks..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd /var/www/sugarclass-aiwriter

# Check container status
echo "📊 Container Status:"
docker-compose ps

# Check backend health
echo ""
echo "🔍 Checking backend health..."
max_attempts=10
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts: Waiting for backend..."
        sleep 3
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ ERROR: Backend health check failed!"
    docker-compose logs backend --tail=50
    exit 1
fi

# Check frontend
echo "🔍 Checking frontend..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "⚠️  Warning: Frontend not responding yet"
fi
ENDSSH
echo ""

# Check if database is empty and populate if needed
echo "📊 Checking database..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd /var/www/sugarclass-aiwriter

# Check article count
ARTICLE_COUNT=$(docker-compose exec -T backend python -c "from database import get_stats; stats = get_stats(); print(stats.get('total_articles', 0))" 2>/dev/null || echo "0")

if [ "$ARTICLE_COUNT" = "0" ]; then
    echo "ℹ️  Database is empty (0 articles)"
    echo "📰 Populating database with articles..."
    docker-compose exec backend python /app/populate_db.py
    echo "✅ Database populated"
else
    echo "✅ Database already has $ARTICLE_COUNT articles"
fi
ENDSSH
echo ""

# Final verification
echo "🎯 Final verification..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd /var/www/sugarclass-aiwriter

echo ""
echo "📊 Final Status:"
docker-compose ps
echo ""

echo "🔗 Access URLs:"
echo "  Frontend:  https://sugarclass.app/aiwriter"
echo "  API:       https://sugarclass.app/aiwriter/api"
echo "  API Docs:  https://sugarclass.app/aiwriter/api/docs"
echo "  Health:    https://sugarclass.app/aiwriter/health"
echo ""

echo "📈 Database Stats:"
docker-compose exec -T backend python -c "from database import get_stats; import json; print(json.dumps(get_stats(), indent=2))" 2>/dev/null || echo "Unable to fetch stats"
ENDSSH
echo ""

echo "✅ Deployment completed successfully!"
echo ""
echo "🎉 Your application is now live at: https://sugarclass.app/aiwriter"
echo ""
echo "ℹ️  SSL Certificate Note:"
echo "   Your existing SSL certificate for sugarclass.app automatically"
echo "   covers the /aiwriter sub-path. No separate certificate needed."
echo ""
echo "📝 Useful Commands:"
echo "  View logs:     ssh root@156.238.242.71 'cd /var/www/sugarclass-aiwriter && docker-compose logs -f'"
echo "  Restart:       ssh root@156.238.242.71 'cd /var/www/sugarclass-aiwriter && docker-compose restart'"
echo "  Check status:  ssh root@156.238.242.71 'cd /var/www/sugarclass-aiwriter && docker-compose ps'"
echo "  Populate DB:  ssh root@156.238.242.71 'cd /var/www/sugarclass-aiwriter && docker-compose exec backend python /app/populate_db.py'"
echo ""
