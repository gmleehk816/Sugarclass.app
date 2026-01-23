#!/bin/bash
# Database backup script for NewsCollect

# Configuration
BACKUP_DIR="/var/www/sugarclass-aiwriter/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="newscollect_backup_${DATE}.sql"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

echo "Starting database backup at $(date)"

# Check if running in Docker
if command -v docker &> /dev/null; then
    # Docker backup
    docker exec newscollect_db pg_dump -U postgres newscollect > "${BACKUP_DIR}/${BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        echo "Backup successful: ${BACKUP_DIR}/${BACKUP_FILE}"
    else
        echo "Backup failed!"
        exit 1
    fi
else
    # Manual PostgreSQL backup
    pg_dump -U newscollect newscollect > "${BACKUP_DIR}/${BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        echo "Backup successful: ${BACKUP_DIR}/${BACKUP_FILE}"
    else
        echo "Backup failed!"
        exit 1
    fi
fi

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"
echo "Backup compressed: ${BACKUP_DIR}/${BACKUP_FILE}.gz"

# Clean old backups (keep last N days)
find ${BACKUP_DIR} -name "newscollect_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "Cleaned backups older than ${RETENTION_DAYS} days"

# Display backup size
ls -lh "${BACKUP_DIR}/${BACKUP_FILE}.gz"

echo "Backup completed at $(date)"
