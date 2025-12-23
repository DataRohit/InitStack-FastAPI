#!/bin/sh

curl -f -s http://localhost:9000/minio/health/live || exit 1
