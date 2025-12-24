#!/bin/bash

set -e

echo "Starting Flower Monitoring Dashboard..."

exec celery -A config.celery_app flower \
    --port="${FLOWER_PORT}" \
    --address="${FLOWER_ADDRESS}" \
    --loglevel="${FLOWER_LOG_LEVEL}" \
    --basic-auth="${FLOWER_BASIC_AUTH}" \
    --url-prefix="${FLOWER_URL_PREFIX}" \
    --max-tasks="${FLOWER_MAX_TASKS}" \
    --persistent="${FLOWER_PERSISTENT}" \
    --db="${FLOWER_DB}" \
    --enable-events="${FLOWER_ENABLE_EVENTS}" \
    --auto-refresh="${FLOWER_AUTO_REFRESH}"
