#!/bin/bash

set -e

echo "Waiting for Elasticsearch to be ready..."
until curl -s -f -u elastic:$ELASTIC_PASSWORD $ELASTICSEARCH_HOSTS/_cluster/health?wait_for_status=yellow&timeout=30s > /dev/null; do
    echo "Elasticsearch is unavailable - sleeping"
    sleep 5
done

echo "Setting up kibana_system user password..."
curl -s -X POST -u elastic:$ELASTIC_PASSWORD "$ELASTICSEARCH_HOSTS/_security/user/kibana_system/_password" \
    -H "Content-Type: application/json" \
    -d "{\"password\":\"$KIBANA_SYSTEM_PASSWORD\"}" || echo "Password already set or user exists"

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
