#!/bin/sh

# Exit On Error
set -o errexit
# Fail On Undefined Variables
set -o nounset

# Wait For Dependencies To Be Ready
echo "Waiting For Dependencies To Be Ready..."
sleep 120

# Run Schema Job
echo "Running Schema Job..."
exec /cassandra-schema/docker.sh
