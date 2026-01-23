# Deployment Guide - SugarClass AI Tutor

This guide covers the deployment of the SugarClass AI Tutor system in both local development and production (VPS) environments.

## 1. Environment Setup

The system uses three main environment files:
- `.env.prod`: Main production environment variables.
- `.env.tutor`: Specific variables for the tutor service.
- `requirements.tutor.txt`: Python dependencies for the backend.

### Required Variables
Ensure the following are set in your `.env.prod`:
- `GOOGLE_API_KEY`: Your Gemini API Key.
- `CONTENT_DB_PASSWORD`: Password for the content PostgreSQL.
- `AGENT_DB_PASSWORD`: Password for the agent/session PostgreSQL.

## 2. Local Deployment (Docker)

The easiest way to run the system is using Docker Compose.

```bash
# Build and start all services
docker-compose -f docker-compose.tutor.yml up -d --build

# View logs
docker-compose -f docker-compose.tutor.yml logs -f

# Stop services
docker-compose -f docker-compose.tutor.yml down
```

### Services & Ports
- **Frontend**: `http://localhost:3000`
- **Tutor Service**: `http://localhost:8001`
- **Qdrant Dashboard**: `http://localhost:6333/dashboard`
- **PostgreSQL (Content)**: `localhost:5433`
- **PostgreSQL (Agent)**: `localhost:5434`

## 3. VPS Deployment

A dedicated deployment script is provided for Ubuntu-based VPS servers.

### Steps:
1. **Prepare Server**: Ensure you have a clean Ubuntu VPS.
2. **Transfer Files**:
   ```bash
   scp -r . root@your-vps-ip:/var/www/sugarclass
   ```
3. **Execute Deployment**:
   ```bash
   ssh root@your-vps-ip
   cd /var/www/sugarclass
   chmod +x scripts/deploy.sh
   sudo ./scripts/deploy.sh
   ```

The script will automatically:
- Install Docker and Docker Compose.
- Install and configure Nginx.
- Set up SSL certificates via Let's Encrypt.
- Build and launch the containers.

## 4. Data Sync & Knowledge Base

The system uses a unique sync mechanism:
1. **Source**: SQLite database in `database/rag_content.db`.
2. **Sync Agent**: Detects changes in the SQLite file.
3. **Migration**: Automatically migrates new content to PostgreSQL.
4. **Vectorization**: Automatically updates the Qdrant vector store.

To manually trigger a migration:
```bash
docker exec -it tutor-sync-agent python scripts/migrate_sqlite_to_postgres.py
```

## 5. Troubleshooting

- **Blank Screen**: Ensure the React frontend built correctly. Check `docker logs tutor-frontend`.
- **API Connection Errors**: Verify that the `tutor-service` is healthy at `http://localhost:8001/tutor/health`.
- **Database Connection**: Ensure the PostgreSQL passwords in `.env.prod` match the database environment variables.
- **Sync Issues**: Check `docker logs tutor-sync-agent` for any migration errors.

---
For further assistance, refer to the `archive/` directory for historical analysis and integration summaries.
