#!/bin/sh

set -e

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting Prometheus initialization..."

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Validating Prometheus configuration..."
promtool check config "${PROMETHEUS_CONFIG_FILE}"

if [ $? -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | ERROR: Prometheus configuration validation failed"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Configuration validation successful"

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Checking rules files..."
for rule_file in /etc/prometheus/rules/*.yml; do
    if [ -f "$rule_file" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Validating rule file: $rule_file"
        promtool check rules "$rule_file"
        if [ $? -ne 0 ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | ERROR: Rule file validation failed: $rule_file"
            exit 1
        fi
    fi
done

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | All rule files validated successfully"

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Setting up storage directory..."
mkdir -p "${PROMETHEUS_STORAGE_TSDB_PATH}"
chown -R nobody:nobody "${PROMETHEUS_STORAGE_TSDB_PATH}"

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Building Prometheus command arguments..."

ARGS=""

if [ "${PROMETHEUS_WEB_ENABLE_LIFECYCLE}" = "true" ]; then
    ARGS="${ARGS} --web.enable-lifecycle"
fi

if [ "${PROMETHEUS_WEB_ENABLE_ADMIN_API}" = "true" ]; then
    ARGS="${ARGS} --web.enable-admin-api"
fi

if [ "${PROMETHEUS_STORAGE_TSDB_WAL_COMPRESSION}" = "true" ]; then
    ARGS="${ARGS} --storage.tsdb.wal-compression"
fi

if [ "${PROMETHEUS_ENABLE_FEATURE_EXEMPLAR_STORAGE}" = "true" ]; then
    ARGS="${ARGS} --enable-feature=exemplar-storage"
fi

if [ "${PROMETHEUS_ENABLE_FEATURE_EXPAND_EXTERNAL_LABELS}" = "true" ]; then
    ARGS="${ARGS} --enable-feature=expand-external-labels"
fi

if [ "${PROMETHEUS_ENABLE_FEATURE_MEMORY_SNAPSHOT_ON_SHUTDOWN}" = "true" ]; then
    ARGS="${ARGS} --enable-feature=memory-snapshot-on-shutdown"
fi

if [ "${PROMETHEUS_ENABLE_FEATURE_PROMQL_AT_MODIFIER}" = "true" ]; then
    ARGS="${ARGS} --enable-feature=promql-at-modifier"
fi

if [ "${PROMETHEUS_ENABLE_FEATURE_PROMQL_NEGATIVE_OFFSET}" = "true" ]; then
    ARGS="${ARGS} --enable-feature=promql-negative-offset"
fi

if [ -n "${PROMETHEUS_TSDB_MIN_BLOCK_DURATION}" ]; then
    ARGS="${ARGS} --storage.tsdb.min-block-duration=${PROMETHEUS_TSDB_MIN_BLOCK_DURATION}"
fi

if [ -n "${PROMETHEUS_TSDB_MAX_BLOCK_DURATION}" ]; then
    ARGS="${ARGS} --storage.tsdb.max-block-duration=${PROMETHEUS_TSDB_MAX_BLOCK_DURATION}"
fi

if [ "${PROMETHEUS_TSDB_ALLOW_OVERLAPPING_BLOCKS}" = "true" ]; then
    ARGS="${ARGS} --storage.tsdb.allow-overlapping-blocks"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting Prometheus server..."
echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Configuration file: ${PROMETHEUS_CONFIG_FILE}"
echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Storage path: ${PROMETHEUS_STORAGE_TSDB_PATH}"
echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Retention time: ${PROMETHEUS_STORAGE_TSDB_RETENTION_TIME}"
echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Retention size: ${PROMETHEUS_STORAGE_TSDB_RETENTION_SIZE}"
echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Web listen address: ${PROMETHEUS_WEB_LISTEN_ADDRESS}"
echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Log level: ${PROMETHEUS_LOG_LEVEL}"

exec prometheus \
    --config.file="${PROMETHEUS_CONFIG_FILE}" \
    --storage.tsdb.path="${PROMETHEUS_STORAGE_TSDB_PATH}" \
    --storage.tsdb.retention.time="${PROMETHEUS_STORAGE_TSDB_RETENTION_TIME}" \
    --storage.tsdb.retention.size="${PROMETHEUS_STORAGE_TSDB_RETENTION_SIZE}" \
    --web.listen-address="${PROMETHEUS_WEB_LISTEN_ADDRESS}" \
    --web.external-url="${PROMETHEUS_WEB_EXTERNAL_URL}" \
    --web.route-prefix="${PROMETHEUS_WEB_ROUTE_PREFIX}" \
    --web.console.templates="${PROMETHEUS_WEB_CONSOLE_TEMPLATES}" \
    --web.console.libraries="${PROMETHEUS_WEB_CONSOLE_LIBRARIES}" \
    --web.page-title="${PROMETHEUS_WEB_PAGE_TITLE}" \
    --web.cors.origin="${PROMETHEUS_WEB_CORS_ORIGIN}" \
    --query.timeout="${PROMETHEUS_QUERY_TIMEOUT}" \
    --query.max-concurrency="${PROMETHEUS_QUERY_MAX_CONCURRENCY}" \
    --query.max-samples="${PROMETHEUS_QUERY_MAX_SAMPLES}" \
    --query.lookback-delta="${PROMETHEUS_QUERY_LOOKBACK_DELTA}" \
    --log.level="${PROMETHEUS_LOG_LEVEL}" \
    --log.format="${PROMETHEUS_LOG_FORMAT}" \
    ${ARGS}
