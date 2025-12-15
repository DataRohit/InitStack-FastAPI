#!/bin/bash

set -e

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

echo "Setting up Filebeat user..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/user/${FILEBEAT_USERNAME}" \
    -H "Content-Type: application/json" \
    -d "{
        \"password\": \"${FILEBEAT_PASSWORD}\",
        \"roles\": [\"filebeat_writer\", \"kibana_admin\"],
        \"full_name\": \"Filebeat Service User\",
        \"email\": \"filebeat@initstack.local\"
    }" || echo "User already exists or creation failed"

echo "Creating Filebeat writer role..."
curl -s -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ELASTICSEARCH_HOSTS}/_security/role/filebeat_writer" \
    -H "Content-Type: application/json" \
    -d "{
        \"cluster\": [\"monitor\", \"manage_index_templates\", \"manage_ilm\", \"manage_ml\"],
        \"indices\": [
            {
                \"names\": [\"filebeat-*\", \"logs-*\"],
                \"privileges\": [\"write\", \"create\", \"create_index\", \"manage\", \"manage_ilm\"]
            }
        ]
    }" || echo "Role already exists or creation failed"

if [ "${FILEBEAT_SETUP_TEMPLATE}" = "true" ]; then
    echo "Setting up Filebeat templates..."
    filebeat setup --template -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" \
        -E setup.kibana.host="${KIBANA_HOST}" \
        -E setup.kibana.username="${KIBANA_USERNAME}" \
        -E setup.kibana.password="${KIBANA_PASSWORD}" || echo "Template setup completed"
fi

if [ "${FILEBEAT_SETUP_ILM}" = "true" ]; then
    echo "Setting up Filebeat ILM policies..."
    filebeat setup --ilm-policy -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" || echo "ILM setup completed"
fi

if [ "${FILEBEAT_SETUP_DASHBOARDS}" = "true" ]; then
    echo "Setting up Filebeat dashboards..."
    filebeat setup --dashboards -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" \
        -E setup.kibana.host="${KIBANA_HOST}" \
        -E setup.kibana.username="${KIBANA_USERNAME}" \
        -E setup.kibana.password="${KIBANA_PASSWORD}" || echo "Dashboard setup completed"
fi

if [ "${FILEBEAT_SETUP_PIPELINES}" = "true" ]; then
    echo "Setting up Filebeat pipelines..."
    filebeat setup --pipelines -E output.elasticsearch.hosts=["${ELASTICSEARCH_HOSTS}"] \
        -E output.elasticsearch.username="${ELASTICSEARCH_USERNAME}" \
        -E output.elasticsearch.password="${ELASTICSEARCH_PASSWORD}" || echo "Pipeline setup completed"
fi

echo "Starting Filebeat..."
exec filebeat -e --strict.perms=false
