#!/bin/sh

set -e

curl -f http://localhost:9187/metrics > /dev/null 2>&1 || exit 1
