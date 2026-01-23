#!/bin/bash

# AI Tutor Deployment Script for VPS
# This script automates the deployment process

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="sugarclass.app"
PROJECT_DIR="/var/www/aitutor"
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"

echo -e "${GREEN}=== AI Tutor Deployment Script ===${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Step 1: Update system
print_info "Updating system packages..."
apt update && apt upgrade -y
print_success "System updated"

# Step 2: Install Docker
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker root
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

# Step 3: Install Docker Compose
print_info "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

# Step 4: Install Nginx
print_info "Checking Nginx installation..."
if ! command -v nginx &> /dev/null; then
    print_info "Installing Nginx..."
    apt install nginx -y
    print_success "Nginx installed"
else
    print_success "Nginx already installed"
fi

# Step 5: Install Certbot
print_info "Checking Certbot installation..."
if ! command -v certbot &> /dev/null; then
    print_info "Installing Certbot..."
    apt install certbot python3-certbot-nginx -y
    print_success "Certbot installed"
else
    print_success "Certbot already installed"
fi

# Step 6: Configure Firewall
print_info "Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
print_success "Firewall configured"

# Step 7: Create project directory
print_info "Creating project directory..."
mkdir -p ${PROJECT_DIR}
print_success "Project directory created: ${PROJECT_DIR}"

# Step 8: Check if .env.prod exists
print_info "Checking environment configuration..."
if [ ! -f "${PROJECT_DIR}/.env.prod" ]; then
    print_error ".env.prod not found!"
    print_error "Please upload .env.prod via SCP before running this script:"
    print_error "  scp .env.prod root@156.238.242.71:${PROJECT_DIR}/"
    exit 1
else
    print_success ".env.prod found"
fi

# Step 9: Check if database exists
print_info "Checking database file..."
if [ ! -f "${PROJECT_DIR}/database/rag_content.db" ]; then
    print_error "Database file not found!"
    print_error "Please upload database via SCP before running this script:"
    print_error "  scp database/rag_content.db root@156.238.242.71:${PROJECT_DIR}/database/"
    exit 1
else
    DB_SIZE=$(du -h "${PROJECT_DIR}/database/rag_content.db" | cut -f1)
    print_success "Database found (size: ${DB_SIZE})"
fi

# Step 10: Create temporary HTTP-only nginx configuration
print_info "Setting up temporary Nginx configuration..."
cat > /etc/nginx/sites-available/${DOMAIN} << EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    # Allow Let's Encrypt ACME challenge
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }

    # Root directory for frontend
    root ${PROJECT_DIR}/html;
    index index.html;

    # Frontend routes - serve SPA
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Proxy backend API requests
    location /api/ {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache_bypass \$http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Proxy API documentation (optional)
    location /docs {
        proxy_pass http://127.0.0.1:8001/docs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
    }

    # OpenAPI JSON (optional)
    location /openapi.json {
        proxy_pass http://127.0.0.1:8001/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Step 11: Enable Nginx site (HTTP-only initially)
print_info "Enabling Nginx site (HTTP-only)..."
ln -sf ${NGINX_CONF} /etc/nginx/sites-enabled/${DOMAIN}
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
print_success "Nginx site enabled (HTTP-only)"

# Step 12: Check and obtain SSL certificate
print_info "Checking SSL certificate..."
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    print_warning "SSL certificate not found"
    print_info "Obtaining SSL certificate..."
    # Stop nginx to free port 80 for certbot
    systemctl stop nginx
    # Use standalone mode to obtain certificate (non-interactive)
    certbot certonly --standalone -d ${DOMAIN} -d www.${DOMAIN} --non-interactive --agree-tos --register-unsafely-without-email
    # Start nginx again
    systemctl start nginx
    print_success "SSL certificate obtained"
else
    print_success "SSL certificate already exists"
fi

# Step 13: Replace with full HTTPS configuration
print_info "Setting up full HTTPS Nginx configuration..."
if [ -f "${PROJECT_DIR}/nginx-prod.conf" ]; then
    cp ${PROJECT_DIR}/nginx-prod.conf ${NGINX_CONF}
    print_success "HTTPS Nginx configuration copied"
else
    print_warning "nginx-prod.conf not found in project directory"
    print_warning "Keeping HTTP-only configuration"
fi

# Test and reload nginx with SSL
nginx -t
systemctl reload nginx
print_success "Nginx reloaded with SSL configuration"

# Step 14: Start Docker containers
print_info "Starting Docker containers..."
cd ${PROJECT_DIR}
docker-compose -f docker-compose.tutor.yml down 2>/dev/null || true
docker-compose -f docker-compose.tutor.yml up -d --build
print_success "Docker containers started"

# Step 15: Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 10
HEALTHY=false
for i in {1..30}; do
    if curl -sf http://localhost:8001/tutor/health > /dev/null 2>&1; then
        print_success "Services are healthy"
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

if [ "$HEALTHY" = false ]; then
    print_warning "Services not fully healthy yet, but deployment completed"
    print_warning "Check logs with: docker-compose -f ${PROJECT_DIR}/docker-compose.tutor.yml logs -f"
fi

# Step 16: Verify deployment
print_info "Verifying deployment..."
echo ""
docker ps | grep tutor
echo ""

# Step 17: Test endpoints
print_info "Testing endpoints..."
echo ""
echo "Testing backend health (API endpoint):"
if curl -sf http://localhost:8001/tutor/health > /dev/null 2>&1; then
    echo "✓ Backend health check passed"
    curl -s http://localhost:8001/tutor/health | head -c 200
else
    print_warning "Backend health check failed - may need more time to initialize"
fi
echo ""
echo ""

echo "Testing frontend (via Nginx):"
if curl -sf http://localhost/ > /dev/null 2>&1; then
    echo "✓ Frontend served successfully"
else
    print_warning "Frontend not responding - check Nginx configuration"
fi
echo ""

# Step 18: Final summary
echo ""
echo -e "${GREEN}=== Deployment Summary ===${NC}"
print_success "Deployment completed successfully!"
echo ""
echo "Service URLs:"
echo "  Frontend: https://${DOMAIN}"
echo "  Backend API: https://${DOMAIN}/api"
echo "  API Docs: https://${DOMAIN}/docs"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose -f ${PROJECT_DIR}/docker-compose.tutor.yml logs -f"
echo "  Restart services: docker-compose -f ${PROJECT_DIR}/docker-compose.tutor.yml restart"
echo "  Update: cd ${PROJECT_DIR} && docker-compose -f docker-compose.tutor.yml up -d --build"
echo ""
echo "Next steps:"
echo "1. Test the application at https://${DOMAIN}"
echo "2. Verify all functionality works"
echo "3. Set up regular backups"
echo "4. Monitor logs and system resources"
echo ""
print_warning "Remember to secure your server:"
echo "  - Change default passwords in .env.prod"
echo "  - Use SSH keys instead of password authentication"
echo "  - Keep the system updated"
echo "  - Monitor logs for suspicious activity"
echo ""
