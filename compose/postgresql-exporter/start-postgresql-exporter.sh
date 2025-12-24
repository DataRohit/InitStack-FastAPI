#!/bin/sh

set -e

CMD="/bin/postgres_exporter"
CMD="$CMD --web.listen-address=$POSTGRES_EXPORTER_WEB_LISTEN_ADDRESS"
CMD="$CMD --web.telemetry-path=$POSTGRES_EXPORTER_WEB_TELEMETRY_PATH"
CMD="$CMD --log.level=$POSTGRES_EXPORTER_LOG_LEVEL"

if [ "$POSTGRES_EXPORTER_AUTO_DISCOVER_DATABASES" = "true" ]; then
    CMD="$CMD --auto-discover-databases"
fi

if [ "$POSTGRES_EXPORTER_EXCLUDE_DATABASES" != "" ]; then
    CMD="$CMD --exclude-databases=$POSTGRES_EXPORTER_EXCLUDE_DATABASES"
fi

exec $CMD
