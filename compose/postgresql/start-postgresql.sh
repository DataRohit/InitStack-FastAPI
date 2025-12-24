#!/bin/bash

set -e

echo "Starting PostgreSQL..."
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"

exec docker-entrypoint.sh postgres \
    -c config_file=/etc/postgresql/postgresql.conf \
    -c hba_file=/etc/postgresql/pg_hba.conf
