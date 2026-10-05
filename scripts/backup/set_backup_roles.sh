#!/bin/bash
set -euo pipefail

# Back up the roles and privileges in the postgreSQL container takeoff-dbt-db
#
# Author: Cesar Gattano
# AI assistant: Claude
# Date: 9 Septembre 2026

# Environment variables
source /home/gattano/Documents/Formation/Takeoff-DBT/.env
TIMESTAMP=$(date +%Y%m%d_%H%M)
CONTAINER="takeoff-dbt-db"

# Create backup directory (if necessary)
mkdir -p "$BACKUP_DIR"

# Backup complet
# -Fc is using zlib to compress the dump file (custom dump format) => pg_restore to restore
# without -FC the dump file is a text file with sql commands => psql to restore
docker exec ${CONTAINER} pg_dumpall -U ${POSTGRES_USER} --globals-only \
    > "$BACKUP_DIR/roles_${TIMESTAMP}.sql"

# Nettoyage : rétention 3h
find "$BACKUP_DIR" -name "roles_*.sql" -mmin +${BACKUP_RETENTION_MINUTES} -delete

echo "Backup $TIMESTAMP on roles done."