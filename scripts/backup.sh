#!/bin/bash

# PostgreSQL backup script for Astro-AA
# This script creates daily backups of the PostgreSQL database

set -e

# Configuration
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DB="${POSTGRES_DB:-astro_aa}"
POSTGRES_USER="${POSTGRES_USER:-astro_user}"
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/astro_aa_backup_$TIMESTAMP.sql"

echo "Starting PostgreSQL backup..."
echo "Database: $POSTGRES_DB"
echo "Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "User: $POSTGRES_USER"
echo "Backup file: $BACKUP_FILE"

# Create the backup
pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose --clean --no-owner --no-privileges > "$BACKUP_FILE"

# Compress the backup
gzip "$BACKUP_FILE"
BACKUP_FILE="$BACKUP_FILE.gz"

echo "Backup completed: $BACKUP_FILE"

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Clean up old backups (keep only last N days)
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "astro_aa_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "Remaining backups:"
ls -lah "$BACKUP_DIR"/astro_aa_backup_*.sql.gz 2>/dev/null || echo "No backups found"

echo "Backup process completed successfully!"