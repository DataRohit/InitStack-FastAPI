#!/bin/bash

set -e

echo "Starting Celery Worker..."

exec celery -A config.celery_app worker \
    --hostname="${CELERY_WORKER_NAME}@%h" \
    --concurrency="${CELERY_WORKER_CONCURRENCY}" \
    --prefetch-multiplier="${CELERY_WORKER_PREFETCH_MULTIPLIER}" \
    --max-tasks-per-child="${CELERY_WORKER_MAX_TASKS_PER_CHILD}" \
    --loglevel="${CELERY_WORKER_LOG_LEVEL}" \
    --time-limit="${CELERY_TASK_TIME_LIMIT}" \
    --soft-time-limit="${CELERY_TASK_SOFT_TIME_LIMIT}"
