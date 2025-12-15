#!/bin/bash

set -e

echo "Sleeping for 30 seconds before starting Kibana..."
sleep 30

echo "Waiting for Elasticsearch to be ready..."
until curl -s -f -u elastic:$ELASTIC_PASSWORD $ELASTICSEARCH_HOSTS/_cluster/health?wait_for_status=yellow&timeout=30s > /dev/null; do
    echo "Elasticsearch is unavailable - sleeping"
    sleep 5
done

echo "Setting up kibana_system user password..."
response=$(curl -s -w "%{http_code}" -X POST -u elastic:$ELASTIC_PASSWORD "$ELASTICSEARCH_HOSTS/_security/user/kibana_system/_password" \
    -H "Content-Type: application/json" \
    -d "{\"password\":\"$KIBANA_SYSTEM_PASSWORD\"}")

http_code="${response: -3}"
if [ "$http_code" = "200" ]; then
    echo "kibana_system password set successfully"
elif [ "$http_code" = "400" ]; then
    echo "kibana_system password already set or validation error"
else
    echo "Failed to set kibana_system password. HTTP code: $http_code"
    echo "Response: ${response%???}"
fi

echo "Elasticsearch is ready - starting Kibana"

echo "Setting up Kibana keystore..."
if [ ! -f /usr/share/kibana/data/kibana.keystore ]; then
    echo "Creating new keystore..."
    yes "" | /usr/share/kibana/bin/kibana-keystore create || echo "Keystore creation completed"
else
    echo "Keystore already exists, skipping creation..."
fi

if ! /usr/share/kibana/bin/kibana-keystore list | grep -q "elasticsearch.password"; then
    echo "Adding Elasticsearch password to keystore..."
    echo "$KIBANA_SYSTEM_PASSWORD" | /usr/share/kibana/bin/kibana-keystore add elasticsearch.password --stdin
fi

if ! /usr/share/kibana/bin/kibana-keystore list | grep -q "xpack.security.encryptionKey"; then
    echo "Adding security encryption key to keystore..."
    echo "$XPACK_SECURITY_ENCRYPTIONKEY" | /usr/share/kibana/bin/kibana-keystore add xpack.security.encryptionKey --stdin
fi

if ! /usr/share/kibana/bin/kibana-keystore list | grep -q "xpack.reporting.encryptionKey"; then
    echo "Adding reporting encryption key to keystore..."
    echo "$XPACK_REPORTING_ENCRYPTIONKEY" | /usr/share/kibana/bin/kibana-keystore add xpack.reporting.encryptionKey --stdin
fi

if ! /usr/share/kibana/bin/kibana-keystore list | grep -q "xpack.encryptedSavedObjects.encryptionKey"; then
    echo "Adding saved objects encryption key to keystore..."
    echo "$XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY" | /usr/share/kibana/bin/kibana-keystore add xpack.encryptedSavedObjects.encryptionKey --stdin
fi

exec /usr/local/bin/kibana-docker
