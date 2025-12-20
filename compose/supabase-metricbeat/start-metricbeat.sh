#!/bin/bash

set -e

echo "Starting Metricbeat for Supabase monitoring..."

cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_NAME}|${METRICBEAT_NAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_HOSTS}|${ELASTICSEARCH_HOSTS}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_USERNAME}|${ELASTICSEARCH_USERNAME}|g" /tmp/metricbeat.yml
sed -i "s|\${ELASTICSEARCH_PASSWORD}|${ELASTICSEARCH_PASSWORD}|g" /tmp/metricbeat.yml
sed -i "s|\${KIBANA_HOST}|${KIBANA_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_LOG_LEVEL}|${METRICBEAT_LOG_LEVEL}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_MONITORING_ENABLED}|${METRICBEAT_MONITORING_ENABLED}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_FIELDS_DATACENTER}|${METRICBEAT_FIELDS_DATACENTER}|g" /tmp/metricbeat.yml
sed -i "s|\${METRICBEAT_HTTP_PORT}|${METRICBEAT_HTTP_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_VECTOR_HOST}|${SUPABASE_VECTOR_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_VECTOR_PORT}|${SUPABASE_VECTOR_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_ANALYTICS_HOST}|${SUPABASE_ANALYTICS_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_ANALYTICS_PORT}|${SUPABASE_ANALYTICS_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_AUTH_HOST}|${SUPABASE_AUTH_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_AUTH_PORT}|${SUPABASE_AUTH_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_SUPAVISOR_HOST}|${SUPABASE_SUPAVISOR_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_SUPAVISOR_PORT}|${SUPABASE_SUPAVISOR_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_STORAGE_HOST}|${SUPABASE_STORAGE_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_STORAGE_PORT}|${SUPABASE_STORAGE_PORT}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_STUDIO_HOST}|${SUPABASE_STUDIO_HOST}|g" /tmp/metricbeat.yml
sed -i "s|\${SUPABASE_STUDIO_PORT}|${SUPABASE_STUDIO_PORT}|g" /tmp/metricbeat.yml
chmod 644 /tmp/metricbeat.yml

echo "Waiting for Elasticsearch to be available..."
until curl -s "${ELASTICSEARCH_HOSTS}/_cluster/health" > /dev/null; do
    echo "Elasticsearch is unavailable - sleeping"
    sleep 30
done
echo "Elasticsearch is available"

echo "Waiting for Kibana to be available..."
until curl -s "${KIBANA_HOST}/api/status" | grep -q '"level":"available"'; do
    echo "Kibana is unavailable - sleeping"
    sleep 30
done
echo "Kibana is available"

echo "Waiting for Supabase Studio to be available..."
until curl -s "${SUPABASE_STUDIO_HOST}:${SUPABASE_STUDIO_PORT}/api/platform/profile" > /dev/null; do
    echo "Supabase Studio is unavailable - sleeping"
    sleep 30
done
echo "Supabase Studio is available"

echo "Starting Metricbeat..."
exec metricbeat -e -c /tmp/metricbeat.yml
