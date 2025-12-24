#!/bin/bash

celery -A config.celery_app inspect ping -d "${CELERY_WORKER_NAME}@${HOSTNAME}" --timeout=10 > /dev/null 2>&1
