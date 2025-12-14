#!/bin/bash

set -e

echo "Starting SonarQube..."
echo "Waiting for PostgreSQL to be ready..."

until timeout 1 bash -c "</dev/tcp/initstack-postgres-service/5432" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 5
done

echo "PostgreSQL is ready - starting SonarQube"

exec /opt/sonarqube/docker/entrypoint.sh
