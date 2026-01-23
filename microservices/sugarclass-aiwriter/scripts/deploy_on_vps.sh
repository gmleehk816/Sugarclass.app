#!/bin/bash

# NewsCollect AI Writer - VPS Deployment Script (Run on VPS)
# This script is meant to be run on the VPS after pulling from GitHub
# Usage: ssh root@156.238.242.71 'cd /var/www/sugarclass-aiwriter && bash scripts/deploy_on_vps.sh'
#
# IMPORTANT: This script adds /aiwriter to the EXISTING sugarclass.app nginx config
# It does NOT create a new server block to avoid conflicts with other apps.

set -e  # Exit immediately on ANY error

echo "🚀 NewsCollect AI Writer - VPS Deployment (On-VPS)"
echo "=================================================="
echo ""

# Configuration
REMOTE_DIR="/var/www/sugarclass-aiwriter"
LOCAL_ENV_FILE="${REMOTE_DIR}/.env"
EXISTING_NGINX_CONF="/etc/nginx/sites-available/sugarclass.app"

echo "📂 Working Directory: ${REMOTE_DIR}"
echo ""

# Check if running on VPS
if [ ! -d "${REMOTE_DIR}" ]; then
    echo "❌ ERROR: Not in correct directory!"
    echo "   Please run this script from: ${REMOTE_DIR}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "${LOCAL_ENV_FILE}" ]; then
    echo "❌ ERROR: .env file not found!"
    echo "   Please create .env file with your configuration."
    echo ""
    echo "Required variables in .env:"
    echo "   POSTGRES_PASSWORD=NewsCollect2024!Secure"
    echo "   POSTGRES_DB=newscollect"
    echo "   POSTGRES_USER=postgres"
    echo "   BACKEND_HOST=0.0.0.0"
    echo "   BACKEND_PORT=8000"
    echo "   NEXT_PUBLIC_API_URL=https://sugarclass.app/aiwriter/api"
    echo "   NEXT_PUBLIC_BASE_PATH=/aiwriter"
    echo "   LLM_BASE_URL=https://hb.dockerspeeds.asia/"
    echo "   LLM_API_KEY=your-api-key"
    echo "   LLM_MODEL=gemini-3-flash-preview"
    echo "   SECRET_KEY=NewsCollect2024!SecretKeyHere"
    echo ""
    exit 1
fi
echo "✅ Found .env file"
echo ""

# Ensure Docker and Docker Compose are installed
echo "🔧 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
echo "✅ Docker and Docker Compose ready"
echo ""

# Stop existing aiwriter containers (if any)
echo "🛑 Stopping existing aiwriter containers..."
docker-compose down 2>/dev/null || true
echo "✅ Containers stopped"
echo ""

# Build and start containers
echo "🔨 Building containers (this may take a few minutes)..."
# Explicitly export variables for docker-compose build args
export $(grep -v '^#' .env | xargs)
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d --remove-orphans

echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo "✅ Services started"
echo ""

# Configure Nginx - Add aiwriter location to existing config
echo "🔧 Configuring Nginx for /aiwriter..."

# Check if existing nginx config exists
if [ ! -f "${EXISTING_NGINX_CONF}" ]; then
    echo "⚠️  Warning: ${EXISTING_NGINX_CONF} not found"
    echo "   Creating a new config from template..."
    cp ${REMOTE_DIR}/nginx/aiwriter.conf ${EXISTING_NGINX_CONF}
else
    # Check if aiwriter locations already exist
    if grep -q "location /aiwriter" "${EXISTING_NGINX_CONF}"; then
        echo "ℹ️  Aiwriter locations already configured in nginx"
    else
        echo "📝 Adding aiwriter locations to existing nginx config..."
        
        # Create the aiwriter location block
        cat > /tmp/aiwriter_locations.conf << 'AIWRITER_EOF'

    # ============================================
    # AI Writer Application (/aiwriter)
    # Added by aiwriter deploy script
    # ============================================
    
    # AI Writer Frontend - with basePath support
    location /aiwriter {
        proxy_pass http://localhost:3000/aiwriter;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # AI Writer API
    location /aiwriter/api/ {
        rewrite ^/aiwriter/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # AI Writer Next.js static files
    location /aiwriter/_next {
        proxy_pass http://localhost:3000/aiwriter/_next;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

AIWRITER_EOF
        
        # Backup the original config
        cp "${EXISTING_NGINX_CONF}" "${EXISTING_NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Insert the aiwriter locations before "# Custom error pages" or at the end
        if grep -q "# Custom error pages" "${EXISTING_NGINX_CONF}"; then
            sed -i '/# Custom error pages/r /tmp/aiwriter_locations.conf' "${EXISTING_NGINX_CONF}"
        else
            # Insert before the last closing brace
            sed -i '/^}$/i\    # AI Writer locations added here' "${EXISTING_NGINX_CONF}"
            sed -i '/# AI Writer locations added here/r /tmp/aiwriter_locations.conf' "${EXISTING_NGINX_CONF}"
        fi
        
        rm /tmp/aiwriter_locations.conf
        echo "✅ Aiwriter locations added to nginx config"
    fi
fi

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
echo ""

# Health checks
echo "🔍 Performing health checks..."

# Check container status
echo "📊 Container Status:"
docker-compose ps
echo ""

# Check backend health
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
if curl -f http://localhost:3000/aiwriter > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "⚠️  Warning: Frontend not responding yet (may still be starting)"
fi
echo ""

# Final verification
echo "🎯 Final verification..."
echo ""
echo "📊 Final Status:"
docker-compose ps
echo ""

echo "🔗 Access URLs:"
echo "  Frontend:  https://sugarclass.app/aiwriter"
echo "  API:       https://sugarclass.app/aiwriter/api"
echo "  API Docs:  https://sugarclass.app/aiwriter/api/docs"
echo "  Health:    https://sugarclass.app/aiwriter/api/health"
echo ""

echo "✅ Deployment completed successfully!"
echo ""
echo "🎉 Your application is now live at: https://sugarclass.app/aiwriter"
echo ""
echo "ℹ️  Notes:"
echo "   - News articles can be loaded using the 'Load News' button in the frontend"
echo "   - SSL is provided by the existing sugarclass.app certificate"
echo ""
echo "📝 Useful Commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Restart:       docker-compose restart"
echo "  Check status:  docker-compose ps"
echo "  Rebuild:       docker-compose build --no-cache && docker-compose up -d"
echo ""
