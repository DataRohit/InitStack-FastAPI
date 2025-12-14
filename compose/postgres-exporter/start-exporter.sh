#!/bin/sh
set -e

echo "Starting PostgreSQL Exporter..."
echo "Waiting for PostgreSQL to be ready..."

while ! nc -z initstack-postgres-service 5432; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is ready - starting exporter"

exec /bin/postgres_exporter \
    --config.file=/etc/postgres_exporter/postgres_exporter.yml \
    --extend.query-path=/etc/postgres_exporter/queries.yml \
    --web.listen-address=:9187 \
    --web.telemetry-path=/metrics \
    --log.level=info \
    --log.format=logfmt \
    --collector.database \
    --collector.locks \
    --collector.replication \
    --collector.replication_slot \
    --collector.stat_bgwriter \
    --collector.stat_database \
    --collector.stat_progress_vacuum \
    --collector.stat_user_tables \
    --collector.statio_user_tables \
    --collector.wal
