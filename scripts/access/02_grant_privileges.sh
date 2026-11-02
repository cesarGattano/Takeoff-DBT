#!/bin/bash

# Script to execute the SQL script 02_grant_privileges.sql in the PostgreSQL container takeoff-dbt-db
# Author: Cesar Gattano
# AI assistant: Claude
# Date: 6 October 2026

source .env

docker exec -i takeoff-dbt-db psql -U postgres -d datawarehouse_e6 \
  -v ON_ERROR_STOP=1 < scripts/access/02_grant_privileges.sql