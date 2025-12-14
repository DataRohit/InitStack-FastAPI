#!/bin/sh

set -e

ARGS="--es.uri=${ES_URI} --es.timeout=${ES_TIMEOUT} --web.listen-address=${WEB_LISTEN_ADDRESS} --web.telemetry-path=${WEB_TELEMETRY_PATH} --log.level=${LOG_LEVEL} --log.format=${LOG_FORMAT} --log.output=${LOG_OUTPUT}"

[ "${ES_ALL}" = "true" ] && ARGS="${ARGS} --es.all"
[ "${ES_INDICES}" = "true" ] && ARGS="${ARGS} --es.indices"
[ "${ES_INDICES_SETTINGS}" = "true" ] && ARGS="${ARGS} --es.indices_settings"
[ "${ES_INDICES_MAPPINGS}" = "true" ] && ARGS="${ARGS} --es.indices_mappings"
[ "${ES_SHARDS}" = "true" ] && ARGS="${ARGS} --es.shards"
[ "${ES_ALIASES}" = "true" ] && ARGS="${ARGS} --es.aliases"
[ "${ES_ILM}" = "true" ] && ARGS="${ARGS} --collector.ilm"
[ "${ES_SLM}" = "true" ] && ARGS="${ARGS} --collector.slm"
[ "${ES_DATA_STREAM}" = "true" ] && ARGS="${ARGS} --collector.data-stream"
[ "${ES_SSL_SKIP_VERIFY}" = "true" ] && ARGS="${ARGS} --es.ssl-skip-verify"
[ "${COLLECTOR_CLUSTERSETTINGS}" = "true" ] && ARGS="${ARGS} --collector.clustersettings"
[ "${COLLECTOR_SNAPSHOTS}" = "true" ] && ARGS="${ARGS} --collector.snapshots"
[ "${COLLECTOR_HEALTH_REPORT}" = "true" ] && ARGS="${ARGS} --collector.health-report"

exec /bin/elasticsearch_exporter ${ARGS}
