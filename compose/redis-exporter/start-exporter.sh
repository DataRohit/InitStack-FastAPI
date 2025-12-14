#!/bin/sh

set -e

exec /redis_exporter \
    --redis.addr="$REDIS_ADDR" \
    --redis.user="$REDIS_USER" \
    --redis.password="$REDIS_PASSWORD" \
    --web.listen-address="$REDIS_EXPORTER_WEB_LISTEN_ADDRESS" \
    --web.telemetry-path="$REDIS_EXPORTER_WEB_TELEMETRY_PATH" \
    --namespace="$REDIS_EXPORTER_NAMESPACE" \
    --connection-timeout="$REDIS_EXPORTER_CONNECTION_TIMEOUT" \
    --log-level="$REDIS_EXPORTER_LOG_LEVEL" \
    --log-format="$REDIS_EXPORTER_LOG_FORMAT" \
    --check-keys-batch-size="$REDIS_EXPORTER_CHECK_KEYS_BATCH_SIZE"
