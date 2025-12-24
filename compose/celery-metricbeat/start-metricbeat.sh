#!/bin/bash

set -e

echo "Starting Metricbeat for Celery monitoring..."

cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_NAME}|${METRICBEAT_NAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_HOSTS}|${ELASTICSEARCH_HOSTS}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_USERNAME}|${ELASTICSEARCH_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_PASSWORD}|${ELASTICSEARCH_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_HOST}|${KIBANA_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_USERNAME}|${KIBANA_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_PASSWORD}|${KIBANA_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${FLOWER_HOST}|${FLOWER_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${FLOWER_PORT}|${FLOWER_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${FLOWER_USERNAME}|${FLOWER_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${FLOWER_PASSWORD}|${FLOWER_PASSWORD}|g" /tmp/metricbeat.yml
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

echo "Waiting for Flower to be available..."
until curl -s "http://${FLOWER_HOST}:${FLOWER_PORT}/" > /dev/null; do
    echo "Flower is unavailable - sleeping"
    sleep 60
done
echo "Flower is available"

echo "Starting Metricbeat..."
exec metricbeat -e -c /tmp/metricbeat.yml
