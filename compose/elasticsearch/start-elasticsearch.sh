#!/bin/bash

set -e

if [ ! -f /usr/share/elasticsearch/config/elasticsearch.keystore ]; then
    echo "Creating elasticsearch keystore..."
    /usr/share/elasticsearch/bin/elasticsearch-keystore create
fi

if ! /usr/share/elasticsearch/bin/elasticsearch-keystore list | grep -q "bootstrap.password"; then
    echo "Setting bootstrap password..."
    echo "$ELASTIC_PASSWORD" | /usr/share/elasticsearch/bin/elasticsearch-keystore add -x "bootstrap.password"
fi

exec /usr/local/bin/docker-entrypoint.sh eswrapper
