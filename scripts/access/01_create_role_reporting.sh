#!/bin/bash

# Script to execute the SQL script 01_create_role_reporting.sql in the PostgreSQL container takeoff-dbt-db
# Author: Cesar Gattano
# AI assistant: Claude
# Date: 5 Octobre 2026

source .env

docker exec -i takeoff-dbt-db psql -U postgres -d datawarehouse_e6 \
  -v ON_ERROR_STOP=1 -v REPORTING_USER=$REPORTING_USER -v REPORTING_PASSWORD=$REPORTING_PASSWORD < scripts/access/01_create_role_reporting.sql