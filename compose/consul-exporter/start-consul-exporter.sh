#!/bin/sh

set -e

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting Consul Exporter initialization..."

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Waiting for Consul to be ready..."
until wget --quiet --tries=1 --timeout=5 -O /dev/null "http://initstack-consul-service:8500/v1/status/leader" 2>/dev/null; do
    echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Consul is not ready yet, waiting..."
    sleep 5
done

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Consul is ready"

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting Consul Exporter..."

if [ "${CONSUL_AGENT_ONLY}" = "true" ]; then
    ARGS="${ARGS} --consul.agent-only"
fi

if [ "${CONSUL_ALLOW_STALE}" = "true" ]; then
    ARGS="${ARGS} --consul.allow_stale"
fi

if [ "${CONSUL_REQUIRE_CONSISTENT}" = "true" ]; then
    ARGS="${ARGS} --consul.require_consistent"
fi

if [ "${CONSUL_HEALTH_SUMMARY}" = "false" ]; then
    ARGS="${ARGS} --no-consul.health-summary"
fi

if [ "${CONSUL_INSECURE}" = "true" ]; then
    ARGS="${ARGS} --consul.insecure"
fi

if [ -n "${KV_PREFIX}" ]; then
    ARGS="${ARGS} --kv.prefix=${KV_PREFIX}"
fi

if [ -n "${KV_FILTER}" ]; then
    ARGS="${ARGS} --kv.filter=${KV_FILTER}"
fi

exec consul_exporter \
    --consul.server="${CONSUL_SERVER}" \
    --consul.timeout="${CONSUL_TIMEOUT}" \
    --consul.request-limit="${CONSUL_REQUEST_LIMIT}" \
    --web.listen-address="${WEB_LISTEN_ADDRESS}" \
    --web.telemetry-path="${WEB_TELEMETRY_PATH}" \
    --log.level="${LOG_LEVEL}" \
    ${ARGS}
