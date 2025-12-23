#!/bin/sh

set -e

exec minio server /data \
    --console-address ":9001" \
    --address ":9000"
