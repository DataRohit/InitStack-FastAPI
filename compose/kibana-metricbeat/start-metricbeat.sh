#!/bin/bash

set -e

echo "Starting Metricbeat for Kibana monitoring..."

cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_NAME}|${METRICBEAT_NAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_HOSTS}|${ELASTICSEARCH_HOSTS}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_USERNAME}|${ELASTICSEARCH_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_PASSWORD}|${ELASTICSEARCH_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_HOST}|${KIBANA_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_MONITOR_HOST}|${KIBANA_MONITOR_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_MONITOR_PORT}|${KIBANA_MONITOR_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_MONITOR_USERNAME}|${KIBANA_MONITOR_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_MONITOR_PASSWORD}|${KIBANA_MONITOR_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_LOG_LEVEL}|${METRICBEAT_LOG_LEVEL}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_MONITORING_ENABLED}|${METRICBEAT_MONITORING_ENABLED}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_FIELDS_DATACENTER}|${METRICBEAT_FIELDS_DATACENTER}|g" /tmp/metricbeat.yml
chmod 644 /tmp/metricbeat.yml

echo "Waiting for Elasticsearch to be available..."
until curl -s "${ELASTICSEARCH_HOSTS}/_cluster/health" > /dev/null; do
    echo "Elasticsearch is unavailable - sleeping"
    sleep 60
done
echo "Elasticsearch is available"

echo "Waiting for Kibana to be available..."
until curl -s "${KIBANA_HOST}/api/status" | grep -q '"level":"available"'; do
    echo "Kibana is unavailable - sleeping"
    sleep 60
done
echo "Kibana is available"

echo "Waiting for Kibana monitoring endpoint to be available..."
until curl -s "http://${KIBANA_MONITOR_HOST}:${KIBANA_MONITOR_PORT}/api/status" > /dev/null; do
    echo "Kibana monitoring endpoint is unavailable - sleeping"
    sleep 60
done
echo "Kibana monitoring endpoint is available"

echo "Starting Metricbeat..."
exec metricbeat -e -c /tmp/metricbeat.yml
