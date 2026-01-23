#!/bin/bash

# =============================================================================
# Sugarclass VPS Setup Script
# =============================================================================

# 1. Update system
echo "Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose
echo "Installing Docker..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-compose-plugin

# 3. Clone repository
echo "Cloning repository..."
if [ -d "Sugarclass.app" ]; then
    cd Sugarclass.app
    git pull
else
    git clone https://github.com/gmleehk816/Sugarclass.app.git
    cd Sugarclass.app
fi

# 4. Prompt for environment variables
echo "Please ensure you have configured the following secrets in your environment or .env files:"
echo "- LLM_API_KEY (AI Tutor)"
echo "- AIWRITER_DB_PASSWORD (AI Writer)"
echo "- SECRET_KEY (Dashboard Backend)"

# 5. Start services
echo "Starting Sugarclass.app in production mode..."
sudo docker compose -f docker-compose.prod.yml up -d --build

echo "Setup complete! Please run the SSL certificate generation command next:"
echo "sudo docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email <your-email> --agree-tos --no-eff-email -d sugarclass.app -d www.sugarclass.app"
