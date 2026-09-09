#!/bin/bash

source .env

# Set up the monitoring database and user in PostgreSQL.
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d postgres -c \
"CREATE DATABASE ${MONITORING_DB}"
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d postgres -c \
"CREATE USER ${MONITORING_USER} WITH PASSWORD '${MONITORING_PASSWORD}'"

# Access management on the database
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d postgres -c \
"GRANT ALL PRIVILEGES ON DATABASE ${MONITORING_DB} TO ${MONITORING_USER}"
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d postgres -c \
"REVOKE ALL ON DATABASE ${POSTGRES_DB} FROM ${MONITORING_USER}"

# Create the SLI measurements table in the monitoring database.
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d ${MONITORING_DB} -c \
"CREATE TABLE sli_measurements ( \
    id SERIAL PRIMARY KEY, \
    sli_name TEXT NOT NULL, \
    measured_at TIMESTAMPTZ NOT NULL DEFAULT now(), \
    value_numeric DOUBLE PRECISION, \
    value_boolean BOOLEAN, \
    success BOOLEAN NOT NULL, \
    error_message TEXT \
)"
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d ${MONITORING_DB} -c \
"CREATE INDEX idx_sli_measurements_name_time ON sli_measurements (sli_name, measured_at DESC)"

# Access management on the SLI measurements table and its sequence
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d ${MONITORING_DB} -c \
"GRANT SELECT, INSERT, UPDATE ON sli_measurements TO ${MONITORING_USER}"
docker exec -it takeoff-dbt-db psql -U ${POSTGRES_USER} -d ${MONITORING_DB} -c \
"GRANT USAGE, SELECT ON SEQUENCE sli_measurements_id_seq TO ${MONITORING_USER}"