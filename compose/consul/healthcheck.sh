#!/bin/sh

set -e

if wget --quiet --tries=1 --timeout=5 -O /dev/null "http://${CONSUL_HOST}:${CONSUL_PORT}/v1/status/leader" 2>/dev/null; then
    if wget --quiet --tries=1 --timeout=5 -O /dev/null "http://${CONSUL_HOST}:${CONSUL_PORT}/ui/" 2>/dev/null; then
        echo "Consul is healthy"
        exit 0
    else
        echo "Consul UI is not responding"
        exit 1
    fi
else
    echo "Consul API is not responding"
    exit 1
fi
