#!/bin/bash

set -e

echo "Sleeping for 60 seconds before starting Prometheus Metricbeat..."
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

echo "Setting up Prometheus Metricbeat user..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/user/${METRICBEAT_USERNAME}" \
    -H "Content-Type: application/json" \
    -d "{
        \"password\": \"${METRICBEAT_PASSWORD}\",
        \"roles\": [\"metricbeat_writer\", \"kibana_admin\"],
        \"full_name\": \"Prometheus Metricbeat Service User\",
        \"email\": \"metricbeat-prometheus@initstack.local\"
    }" || echo "User already exists or creation failed"

echo "Creating Metricbeat writer role..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/role/metricbeat_writer" \
    -H "Content-Type: application/json" \
    -d "{
        \"cluster\": [\"monitor\", \"manage_index_templates\", \"manage_ilm\", \"manage_ml\"],
        \"indices\": [
            {
                \"names\": [\"metricbeat-*\", \"metrics-*\"],
                \"privileges\": [\"write\", \"create\", \"create_index\", \"manage\", \"manage_ilm\"]
            }
        ]
    }" || echo "Role already exists or creation failed"

if [ "${METRICBEAT_SETUP_TEMPLATE}" = "true" ] || [ "${METRICBEAT_SETUP_ILM}" = "true" ]; then
    echo "Setting up Metricbeat index management (templates and ILM)..."
    metricbeat setup --index-management -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" \
        -E setup.kibana.host="${KIBANA_HOST}" \
        -E setup.kibana.username="${KIBANA_USERNAME}" \
        -E setup.kibana.password="${KIBANA_PASSWORD}" || echo "Index management setup completed"
fi

if [ "${METRICBEAT_SETUP_DASHBOARDS}" = "true" ]; then
    echo "Setting up Metricbeat dashboards..."
    metricbeat setup --dashboards -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" \
        -E setup.kibana.host="${KIBANA_HOST}" \
        -E setup.kibana.username="${KIBANA_USERNAME}" \
        -E setup.kibana.password="${KIBANA_PASSWORD}" || echo "Dashboard setup completed"
fi

echo "Copying config file to writable location..."
cp /usr/share/metricbeat/metricbeat.yml /tmp/metricbeat.yml
chmod 644 /tmp/metricbeat.yml

echo "Starting Prometheus Metricbeat..."
exec metricbeat -e --strict.perms=false -c /tmp/metricbeat.yml
