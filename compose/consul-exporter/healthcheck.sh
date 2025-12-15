#!/bin/sh

set -e

if timeout 5 sh -c "echo > /dev/tcp/${EXPORTER_HOST}/${EXPORTER_PORT}" 2>/dev/null; then
    if wget --quiet --tries=1 --timeout=5 -O /dev/null "http://${EXPORTER_HOST}:${EXPORTER_PORT}${TELEMETRY_PATH}" 2>/dev/null; then
        echo "Consul Exporter is healthy"
        exit 0
    else
        echo "Consul Exporter metrics endpoint is not responding"
        exit 1
    fi
else
    echo "Consul Exporter is not responding on port ${EXPORTER_PORT}"
    exit 1
fi
