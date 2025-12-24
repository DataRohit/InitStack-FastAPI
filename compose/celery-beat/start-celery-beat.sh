#!/bin/bash

set -e

echo "Starting Celery Beat Scheduler..."

exec celery -A config.celery_app beat \
    --scheduler="${CELERY_BEAT_SCHEDULER}" \
    --schedule="${CELERY_BEAT_SCHEDULE_FILENAME}" \
    --loglevel="${CELERY_BEAT_LOG_LEVEL}"
