#!/bin/bash

# =============================================================================
# Sugarclass.app - Quick Update Script
# =============================================================================

# Define project directory
PROJECT_DIR="/var/www/Sugarclass.app"

echo "🚀 Starting Update Process..."

# 1. Navigate to project directory
cd $PROJECT_DIR || exit

# 2. Pull latest changes from GitHub
echo "⏬ Pulling latest changes from main branch..."
# Using --no-rebase to ensure a clean pull
git pull origin main

# 3. Rebuild and restart services
echo "🏗️  Rebuilding and restarting production services..."
# We use --build to ensure all changes in Dockerfiles/Source code are picked up
docker compose -f docker-compose.prod.yml up -d --build

# 4. Cleanup old images
echo "🧹 Cleaning up old images to save space..."
docker image prune -f

echo "✅ Update Complete! Sugarclass.app is running the latest version."
