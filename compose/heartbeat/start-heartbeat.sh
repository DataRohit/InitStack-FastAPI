#!/bin/bash

set -e

echo "Sleeping for 60 seconds before starting Heartbeat..."
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

echo "Setting up Heartbeat user..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/user/${HEARTBEAT_USERNAME}" \
    -H "Content-Type: application/json" \
    -d "{
        \"password\": \"${HEARTBEAT_PASSWORD}\",
        \"roles\": [\"heartbeat_writer\", \"kibana_admin\"],
        \"full_name\": \"Heartbeat Service User\",
        \"email\": \"heartbeat@initstack.local\"
    }" || echo "User already exists or creation failed"

echo "Creating Heartbeat writer role..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/role/heartbeat_writer" \
    -H "Content-Type: application/json" \
    -d "{
        \"cluster\": [\"monitor\", \"manage_index_templates\", \"manage_ilm\"],
        \"indices\": [
            {
                \"names\": [\"heartbeat-*\", \"uptime-*\"],
                \"privileges\": [\"write\", \"create\", \"create_index\", \"manage\", \"manage_ilm\"]
            }
        ]
    }" || echo "Role already exists or creation failed"

if [ "${HEARTBEAT_SETUP_TEMPLATE}" = "true" ] || [ "${HEARTBEAT_SETUP_ILM}" = "true" ]; then
    echo "Setting up Heartbeat index management (templates and ILM)..."
    heartbeat setup --index-management -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" \
        -E setup.kibana.host="${KIBANA_HOST}" \
        -E setup.kibana.username="${KIBANA_USERNAME}" \
        -E setup.kibana.password="${KIBANA_PASSWORD}" || echo "Index management setup completed"
fi

if [ "${HEARTBEAT_SETUP_DASHBOARDS}" = "true" ]; then
    echo "Setting up Heartbeat dashboards..."
    heartbeat setup --dashboards -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" \
        -E setup.kibana.host="${KIBANA_HOST}" \
        -E setup.kibana.username="${KIBANA_USERNAME}" \
        -E setup.kibana.password="${KIBANA_PASSWORD}" || echo "Dashboard setup completed"
fi

echo "Copying config file to writable location..."
cp /usr/share/heartbeat/heartbeat.yml /tmp/heartbeat.yml
chmod 644 /tmp/heartbeat.yml

echo "Starting Heartbeat..."
exec heartbeat -e --strict.perms=false -c /tmp/heartbeat.yml
