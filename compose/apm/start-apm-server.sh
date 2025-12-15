#!/bin/bash

set -e

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting APM Server initialization..."

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Waiting for Elasticsearch to be ready..."
ES_HOST=$(echo "${ELASTICSEARCH_HOSTS}" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f1)
ES_PORT=$(echo "${ELASTICSEARCH_HOSTS}" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f2 | cut -d'/' -f1)

until timeout 5 bash -c "</dev/tcp/${ES_HOST}/${ES_PORT}" 2>/dev/null; do
    echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Elasticsearch is not ready yet, waiting..."
    sleep 10
done

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Elasticsearch is ready"

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Waiting for Kibana to be ready..."
KIBANA_HOST_ONLY=$(echo "${KIBANA_HOST}" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f1)
KIBANA_PORT=$(echo "${KIBANA_HOST}" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f2 | cut -d'/' -f1)

until timeout 5 bash -c "</dev/tcp/${KIBANA_HOST_ONLY}/${KIBANA_PORT}" 2>/dev/null; do
    echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Kibana is not ready yet, waiting..."
    sleep 10
done

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Kibana is ready"

echo "$(date '+%Y-%m-%d %H:%M:%S.%3N') | Starting APM Server..."
exec apm-server -e -c /usr/share/apm-server/apm-server.yml
