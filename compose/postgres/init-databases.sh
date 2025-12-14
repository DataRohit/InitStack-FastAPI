#!/usr/bin/env bash

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE sonarqube_db;
    GRANT ALL PRIVILEGES ON DATABASE sonarqube_db TO $POSTGRES_USER;

    CREATE USER postgres_exporter WITH PASSWORD 'Kx9mP2nQ7wR5tY8u';
    ALTER USER postgres_exporter SET SEARCH_PATH TO postgres_exporter,pg_catalog;

    GRANT CONNECT ON DATABASE $POSTGRES_DB TO postgres_exporter;
    GRANT CONNECT ON DATABASE sonarqube_db TO postgres_exporter;
    GRANT pg_monitor TO postgres_exporter;

    CREATE SCHEMA IF NOT EXISTS postgres_exporter;
    GRANT USAGE ON SCHEMA postgres_exporter TO postgres_exporter;
EOSQL
