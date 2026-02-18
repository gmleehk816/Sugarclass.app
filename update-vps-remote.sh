#!/bin/bash

# =============================================================================
# Sugarclass.app - Optimized Update Script
# =============================================================================
# Handles smart rebuilds for all 5 microservices:
#   - aiwriter (AI Writer)
#   - tutor (AI Tutor)
#   - aiexaminer (AI Examiner)
#   - aimaterials (AI Materials)
#   - sugarclass (Main Dashboard)
#
# Usage:
#   ./update-vps-remote.sh              # Smart rebuild (only changed services)
#   ./update-vps-remote.sh --full       # Full rebuild (no cache)
#   ./update-vps-remote.sh --no-cache   # Rebuild changed services without cache
# =============================================================================

# Define project directory
PROJECT_DIR="/var/www/Sugarclass.app"

# Parse arguments
FULL_REBUILD=false
NO_CACHE=false
for arg in "$@"; do
    case $arg in
        --full)
            FULL_REBUILD=true
            ;;
        --no-cache)
            NO_CACHE=true
            ;;
        --help)
            echo "Usage: $0 [--full] [--no-cache]"
            echo "  --full      Rebuild all services from scratch"
            echo "  --no-cache  Build changed services without cache"
            exit 0
            ;;
    esac
done

echo "🚀 Starting Update Process..."

# 1. Navigate to project directory
cd $PROJECT_DIR || exit

# 2. Pull latest changes from GitHub
echo "⏬ Pulling latest changes from main branch..."
git pull origin main

# 3. Detect what microservices changed
echo "🔍 Detecting changed microservices..."
CHANGED_FILES=$(git diff HEAD@{1} --name-only)

# Track which services and components changed
declare -A BACKEND_CHANGED
declare -A FRONTEND_CHANGED
SERVICES=("aiwriter" "tutor" "aiexaminer" "aimaterials" "sugarclass")

for service in "${SERVICES[@]}"; do
    BACKEND_CHANGED[$service]=false
    FRONTEND_CHANGED[$service]=false
done

# Declare global flag for compose changes
COMPOSE_CHANGED=false
if echo "$CHANGED_FILES" | grep -qE "docker-compose.*\.yml"; then
    COMPOSE_CHANGED=true
    echo "  ! docker-compose config changed"
fi

# Detect changes for each microservice
detect_changes() {
    local service=$1
    local path_prefix="microservices/sugarclass-$service/"
    local frontend_path_pattern="^$path_prefix(frontend/|app/frontend/)"
    local backend_path_pattern="^$path_prefix(app/|backend/|scripts/|Dockerfile|Dockerfile.backend|\.env|requirements\.txt|start\.py)"

    # Backend changes:
    # 1. Any file in service root (except frontend/)
    # 2. Specifically Dockerfile, Dockerfile.backend, requirements.txt, .env
    # 3. Any file in app/ or backend/ (if they exist)
    local backend_changed_files
    backend_changed_files=$(echo "$CHANGED_FILES" | grep -E "$backend_path_pattern" | grep -vE "$frontend_path_pattern" || true)
    if [ -n "$backend_changed_files" ]; then
        BACKEND_CHANGED[$service]=true
        echo "  ✓ $service-backend changed"
    fi

    # Frontend changes:
    # 1. Any file in frontend/ subdirectory
    # 2. AI Materials style frontend path under app/frontend/
    if echo "$CHANGED_FILES" | grep -qE "$frontend_path_pattern"; then
        FRONTEND_CHANGED[$service]=true
        echo "  ✓ $service-frontend changed"
    fi
}

# Check main sugarclass app separately
if echo "$CHANGED_FILES" | grep -qE "^(backend/|frontend/|Dockerfile)"; then
    if echo "$CHANGED_FILES" | grep -qE "^(backend/|Dockerfile)"; then
        BACKEND_CHANGED[sugarclass]=true
        echo "  ✓ sugarclass-backend changed"
    fi
    if echo "$CHANGED_FILES" | grep -qE "^frontend/"; then
        FRONTEND_CHANGED[sugarclass]=true
        echo "  ✓ sugarclass-frontend changed"
    fi
fi

# Check microservices
for service in aiwriter tutor aiexaminer aimaterials; do
    detect_changes $service
done

# 4. Build changed services
BUILD_ARGS=""
if [ "$FULL_REBUILD" = true ] || [ "$NO_CACHE" = true ]; then
    BUILD_ARGS="--no-cache"
fi

echo ""
echo "🏗️  Building changed services..."
echo ""

# Track services to build
SERVICES_TO_BUILD=()

for service in "${SERVICES[@]}"; do
    if [ "$FULL_REBUILD" = true ] || [ "$COMPOSE_CHANGED" = true ]; then
        # Build all services
        case $service in
            aiwriter)
                SERVICES_TO_BUILD+=("aiwriter-backend" "aiwriter-frontend")
                ;;
            tutor)
                SERVICES_TO_BUILD+=("tutor-backend" "tutor-frontend")
                ;;
            aiexaminer)
                SERVICES_TO_BUILD+=("aiexaminer-backend" "aiexaminer-frontend")
                ;;
            aimaterials)
                SERVICES_TO_BUILD+=("aimaterials-backend" "aimaterials-frontend")
                ;;
            sugarclass)
                SERVICES_TO_BUILD+=("backend" "frontend")
                ;;
        esac
    else
        # Build only changed components
        if [ "${BACKEND_CHANGED[$service]}" = true ] || [ "${FRONTEND_CHANGED[$service]}" = true ]; then
            case $service in
                aiwriter)
                    [ "${BACKEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("aiwriter-backend")
                    [ "${FRONTEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("aiwriter-frontend")
                    ;;
                tutor)
                    [ "${BACKEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("tutor-backend")
                    [ "${FRONTEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("tutor-frontend")
                    ;;
                aiexaminer)
                    [ "${BACKEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("aiexaminer-backend")
                    [ "${FRONTEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("aiexaminer-frontend")
                    ;;
                aimaterials)
                    [ "${BACKEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("aimaterials-backend")
                    [ "${FRONTEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("aimaterials-frontend")
                    ;;
                sugarclass)
                    [ "${BACKEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("backend")
                    [ "${FRONTEND_CHANGED[$service]}" = true ] && SERVICES_TO_BUILD+=("frontend")
                    ;;
            esac
        fi
    fi
done

# Build services
if [ ${#SERVICES_TO_BUILD[@]} -gt 0 ]; then
    echo "Building: ${SERVICES_TO_BUILD[*]}"
    docker compose -f docker-compose.prod.yml build $BUILD_ARGS "${SERVICES_TO_BUILD[@]}"
    docker compose -f docker-compose.prod.yml up -d "${SERVICES_TO_BUILD[@]}"
    
    # Restart gateway to refresh upstream DNS (prevents 502 errors from stale IPs)
    echo ""
    echo "🔄 Restarting gateway to refresh upstream connections..."
    docker restart sugarclass-gateway
else
    echo "ℹ️  No services changed. Skipping build."
fi

# 5. Only restart gateway nginx if needed (gateway config changes)
if echo "$CHANGED_FILES" | grep -qE "gateway/nginx/"; then
    echo ""
    echo "🔄 Restarting gateway nginx (config changed)..."
    docker compose -f docker-compose.prod.yml restart nginx
fi

# 6. Cleanup old images
echo ""
echo "🧹 Cleaning up old images to save space..."
docker image prune -f

echo ""
echo "✅ Update Complete! Sugarclass.app is running the latest version."
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.prod.yml ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}" | grep -E "NAME|frontend|backend|nginx"
