#!/bin/bash

set -e

if timeout 5 bash -c "</dev/tcp/${APM_SERVER_HOST}/${APM_SERVER_PORT}" 2>/dev/null; then
    echo "APM Server is healthy"
    exit 0
else
    echo "APM Server is not responding"
    exit 1
fi
