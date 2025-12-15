#!/bin/bash

set -e

echo "Starting Metricbeat for Exporters monitoring..."

cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_NAME}|${METRICBEAT_NAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_HOSTS}|${ELASTICSEARCH_HOSTS}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_USERNAME}|${ELASTICSEARCH_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_PASSWORD}|${ELASTICSEARCH_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_HOST}|${KIBANA_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${CONSUL_EXPORTER_HOST}|${CONSUL_EXPORTER_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${CONSUL_EXPORTER_PORT}|${CONSUL_EXPORTER_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${POSTGRES_EXPORTER_HOST}|${POSTGRES_EXPORTER_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${POSTGRES_EXPORTER_PORT}|${POSTGRES_EXPORTER_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${REDIS_EXPORTER_HOST}|${REDIS_EXPORTER_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${REDIS_EXPORTER_PORT}|${REDIS_EXPORTER_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_EXPORTER_HOST}|${ELASTICSEARCH_EXPORTER_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_EXPORTER_PORT}|${ELASTICSEARCH_EXPORTER_PORT}|g" /tmp/metricbeat.yml
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

echo "Waiting for Consul Exporter to be available..."
until curl -s "http://${CONSUL_EXPORTER_HOST}:${CONSUL_EXPORTER_PORT}/metrics" > /dev/null; do
    echo "Consul Exporter is unavailable - sleeping"
    sleep 60
done
echo "Consul Exporter is available"

echo "Waiting for PostgreSQL Exporter to be available..."
until curl -s "http://${POSTGRES_EXPORTER_HOST}:${POSTGRES_EXPORTER_PORT}/metrics" > /dev/null; do
    echo "PostgreSQL Exporter is unavailable - sleeping"
    sleep 60
done
echo "PostgreSQL Exporter is available"

echo "Waiting for Redis Exporter to be available..."
until curl -s "http://${REDIS_EXPORTER_HOST}:${REDIS_EXPORTER_PORT}/metrics" > /dev/null; do
    echo "Redis Exporter is unavailable - sleeping"
    sleep 60
done
echo "Redis Exporter is available"

echo "Waiting for Elasticsearch Exporter to be available..."
until curl -s "http://${ELASTICSEARCH_EXPORTER_HOST}:${ELASTICSEARCH_EXPORTER_PORT}/metrics" > /dev/null; do
    echo "Elasticsearch Exporter is unavailable - sleeping"
    sleep 60
done
echo "Elasticsearch Exporter is available"

echo "Starting Metricbeat..."
exec metricbeat -e -c /tmp/metricbeat.yml
