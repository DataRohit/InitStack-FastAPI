#!/bin/bash

set -e

echo "Starting Metricbeat for Elastic Stack monitoring..."

cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_NAME}|${METRICBEAT_NAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_HOSTS}|${ELASTICSEARCH_HOSTS}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_USERNAME}|${ELASTICSEARCH_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_PASSWORD}|${ELASTICSEARCH_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_HOST}|${KIBANA_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${FILEBEAT_HOST}|${FILEBEAT_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${FILEBEAT_PORT}|${FILEBEAT_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${APM_HOST}|${APM_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${APM_PORT}|${APM_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${HEARTBEAT_HOST}|${HEARTBEAT_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${HEARTBEAT_PORT}|${HEARTBEAT_PORT}|g" /tmp/metricbeat.yml
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

echo "Waiting for Filebeat to be available..."
until curl -s "http://${FILEBEAT_HOST}:${FILEBEAT_PORT}/stats" > /dev/null; do
    echo "Filebeat is unavailable - sleeping"
    sleep 60
done
echo "Filebeat is available"

echo "Waiting for APM Server to be available..."
until curl -s "http://${APM_HOST}:${APM_PORT}/" > /dev/null; do
    echo "APM Server is unavailable - sleeping"
    sleep 60
done
echo "APM Server is available"

echo "Waiting for Heartbeat to be available..."
until curl -s "http://${HEARTBEAT_HOST}:${HEARTBEAT_PORT}/stats" > /dev/null; do
    echo "Heartbeat is unavailable - sleeping"
    sleep 60
done
echo "Heartbeat is available"

echo "Starting Metricbeat..."
exec metricbeat -e -c /tmp/metricbeat.yml
