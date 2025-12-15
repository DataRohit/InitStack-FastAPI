#!/bin/bash

set -e

APM_HOST="${APM_SERVER_HOST:-0.0.0.0}"
APM_PORT="${APM_SERVER_PORT:-8200}"

if timeout 5 bash -c "</dev/tcp/${APM_HOST}/${APM_PORT}" 2>/dev/null; then
    echo "APM Server is healthy"
    exit 0
else
    echo "APM Server is not responding"
    exit 1
fi
