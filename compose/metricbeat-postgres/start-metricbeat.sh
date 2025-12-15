#!/bin/bash

set -e

echo "Sleeping for 60 seconds before starting PostgreSQL Metricbeat..."
sleep 60

echo "Waiting for Elasticsearch to be ready..."
until curl -s -f -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} ${ELASTICSEARCH_HOSTS}/_cluster/health?wait_for_status=yellow&timeout=30s > /dev/null; do
    echo "Elasticsearch is unavailable - sleeping"
    sleep 5
done

echo "Waiting for Kibana to be ready..."
until curl -s -f -u ${KIBANA_USERNAME}:${KIBANA_PASSWORD} ${KIBANA_HOST}/api/status > /dev/null; do
    echo "Kibana is unavailable - sleeping"
    sleep 5
done

echo "Setting up PostgreSQL Metricbeat user..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/user/${METRICBEAT_USERNAME}" \
    -H "Content-Type: application/json" \
    -d "{
        \"password\": \"${METRICBEAT_PASSWORD}\",
        \"roles\": [\"metricbeat_writer\", \"kibana_admin\"],
        \"full_name\": \"PostgreSQL Metricbeat Service User\",
        \"email\": \"metricbeat-postgres@initstack.local\"
    }" || echo "User already exists or creation failed"

echo "Copying config file to writable location..."
cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
chmod 644 /tmp/metricbeat.yml

echo "Starting PostgreSQL Metricbeat..."
exec metricbeat -e --strict.perms=false -c /tmp/metricbeat.yml
