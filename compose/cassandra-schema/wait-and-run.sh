#!/bin/sh

echo "Cassandra Is Healthy! Sleeping Additional 60 Seconds Before Running Schema Job..."
sleep 60

echo "Running Schema Job..."
exec /cassandra-schema/docker.sh
