#!/bin/bash

# =============================================================================
# Sugarclass.app - Quick Update Script
# =============================================================================
# Handles smart rebuilds for all 5 microservices:
#   - aiwriter (AI Writer)
#   - tutor (AI Tutor)
#   - aiexaminer (AI Examiner)
#   - aimaterials (AI Materials)
#   - sugarclass (Main Dashboard)
# =============================================================================

# Define project directory
PROJECT_DIR="/var/www/Sugarclass.app"

echo "🚀 Starting Update Process..."

# 1. Navigate to project directory
cd $PROJECT_DIR || exit

# 2. Pull latest changes from GitHub
echo "⏬ Pulling latest changes from main branch..."
git pull origin main

# 3. Detect what microservices changed
echo "🔍 Detecting changed microservices..."
CHANGED_FILES=$(git diff HEAD@{1} --name-only)

# Track which services changed (including -backend and -frontend)
declare -A SERVICES_CHANGED
SERVICES_CHANGED[aiwriter]=false
SERVICES_CHANGED[tutor]=false
SERVICES_CHANGED[aiexaminer]=false
SERVICES_CHANGED[aimaterials]=false
SERVICES_CHANGED[sugarclass]=false

# Check each microservice
for service in aiwriter tutor aiexaminer aimaterials sugarclass; do
    if echo "$CHANGED_FILES" | grep -q "microservices/sugarclass-$service"; then
        SERVICES_CHANGED[$service]=true
        echo "  ✓ $service changed"
    fi
done

# 4. Force rebuild changed microservices (no cache)
echo ""
echo "🏗️  Rebuilding changed microservices (no cache)..."
for service in "${!SERVICES_CHANGED[@]}"; do
    if [ "${SERVICES_CHANGED[$service]}" = true ]; then
        case $service in
            aiwriter)
                SERVICES="aiwriter-backend aiwriter-frontend"
                ;;
            tutor)
                SERVICES="tutor-backend tutor-frontend"
                ;;
            aiexaminer)
                SERVICES="aiexaminer-backend aiexaminer-frontend"
                ;;
            aimaterials)
                SERVICES="aimaterials-backend aimaterials-frontend"
                ;;
            sugarclass)
                SERVICES="backend frontend"
                ;;
        esac
        echo "  → Rebuilding $service..."
        docker compose -f docker-compose.prod.yml build --no-cache $SERVICES
        docker compose -f docker-compose.prod.yml up -d $SERVICES
    fi
done

# 5. Rebuild and restart all services with normal build
echo ""
echo "🔄 Rebuilding and restarting all services (with cache)..."
docker compose -f docker-compose.prod.yml up -d --build

# 6. Cleanup old images
echo ""
echo "🧹 Cleaning up old images to save space..."
docker image prune -f

echo ""
echo "✅ Update Complete! Sugarclass.app is running the latest version."
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.prod.yml ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}" | grep -E "NAME|frontend|backend"
