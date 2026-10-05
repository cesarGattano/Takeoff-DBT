#!/bin/bash

# Script to execute the SQL script 00_audit.sql in the PostgreSQL container takeoff-dbt-db
# Author: Cesar Gattano
# AI assistant: Claude
# Date: 9 September 2026

docker exec -i takeoff-dbt-db psql -U postgres -d datawarehouse_e6 \
  -v ON_ERROR_STOP=1 < scripts/access/00_audit.sql