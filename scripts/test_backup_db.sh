#!/bin/bash
set -euo pipefail

# Test of the database back up in a removable postgreSQL container
#
# Author: Cesar Gattano
# AI assistant: Claude
# Date: 10 Septembre 2026

if [ ! $# == 2 ]; then
    echo "Missing arguments: 2 required roles_*.sql and full_*.dump to restore"
    exit 1
fi

DUMP_ROLES_FILE=$1
DUMP_DB_FILE=$2

if [ ! -f $DUMP_ROLES_FILE ]; then
    echo "File $DUMP_ROLES_FILE not found!"
    exit 1
else
    echo "Restore from file $DUMP_ROLES_FILE"
fi

if [ ! -f $DUMP_DB_FILE ]; then
    echo "File $DUMP_DB_FILE not found!"
    exit 1
else
    echo "Restore from file $DUMP_DB_FILE"
fi


# Environment variables
source /home/gattano/Documents/Formation/Takeoff-DBT/.env
TIMESTAMP=$(date +%Y%m%d_%H%M)
TEST_CONTAINER="pg-restore-test"
TEST_LOCAL_DB_PORT=5434

echo "Create a container for the test..."
docker run -d --name ${TEST_CONTAINER} \
  -e POSTGRES_USER=${POSTGRES_USER} \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
  -e POSTGRES_DB=${POSTGRES_DB} \
  -p ${TEST_LOCAL_DB_PORT}:${POSTGRES_PORT} \
  postgres:18.6-alpine3.24

# attendre que le conteneur soit prêt
sleep 5

# Copy dump/sql files in the docker
docker cp "$DUMP_ROLES_FILE" pg-restore-test:/tmp/roles.sql
docker cp "$DUMP_DB_FILE" pg-restore-test:/tmp/restore.dump
 
# Restore the roles (psql)
docker exec -t ${TEST_CONTAINER} psql -U ${POSTGRES_USER} -f /tmp/roles.sql

# Restore data and rights
docker exec -i ${TEST_CONTAINER} pg_restore -U ${POSTGRES_USER} -d ${POSTGRES_DB} /tmp/restore.dump

echo "Restoration done."
echo "Validation starts..."

# Vérification
echo "Verification of the restored roles:"
docker exec -t ${TEST_CONTAINER} psql -U ${POSTGRES_USER} -tAc "\du"

echo "Verification of the rights on fact_commandes table:"
docker exec -t ${TEST_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tAc "\dp fact_commandes"

echo "Verification of the number of entries in each table:"
docker exec -t ${TEST_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tAc \
  "SELECT 'fact_commandes' as table_name, COUNT(*) FROM fact_commandes
  UNION ALL
  SELECT 'fact_visites', COUNT(*) FROM fact_visites
  UNION ALL
  SELECT 'dim_canal', COUNT(*) FROM dim_canal
  UNION ALL
  SELECT 'dim_client', COUNT(*) FROM dim_client
  UNION ALL
  SELECT 'dim_date', COUNT(*) FROM dim_date
  UNION ALL
  SELECT 'dim_produit', COUNT(*) FROM dim_produit
  UNION ALL
  SELECT 'dim_statut_commande', COUNT(*) FROM dim_statut_commande;"

echo "Run DBT tests on restored database"
dbt test --profiles-dir .dbt --target restore_test

# nettoyage
echo "Cleaning removable docker..."
docker rm -f pg-restore-test

exit 0