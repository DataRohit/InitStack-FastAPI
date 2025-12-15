#!/bin/sh

set -e

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting Consul initialization..."

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Creating Consul data directory..."
mkdir -p /consul/data
chown -R consul:consul /consul/data

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting Consul server..."
exec consul agent \
    -server \
    -bootstrap-expect=1 \
    -datacenter="${CONSUL_DATACENTER}" \
    -data-dir=/consul/data \
    -node="${CONSUL_NODE_NAME}" \
    -bind="${CONSUL_BIND_ADDR}" \
    -client="${CONSUL_CLIENT_ADDR}" \
    -retry-join=127.0.0.1 \
    -ui \
    -log-level="${CONSUL_LOG_LEVEL}"
