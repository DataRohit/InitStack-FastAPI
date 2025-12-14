#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE sonarqube_db;
    GRANT ALL PRIVILEGES ON DATABASE sonarqube_db TO $POSTGRES_USER;
EOSQL
