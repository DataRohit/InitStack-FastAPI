#!/bin/sh

set -e

sed -e "s/\${HAPROXY_MAX_CONNECTIONS}/${HAPROXY_MAX_CONNECTIONS}/g" \
    -e "s/\${HAPROXY_TIMEOUT_CONNECT}/${HAPROXY_TIMEOUT_CONNECT}/g" \
    -e "s/\${HAPROXY_TIMEOUT_CLIENT}/${HAPROXY_TIMEOUT_CLIENT}/g" \
    -e "s/\${HAPROXY_TIMEOUT_SERVER}/${HAPROXY_TIMEOUT_SERVER}/g" \
    -e "s/\${HAPROXY_STATS_PORT}/${HAPROXY_STATS_PORT}/g" \
    -e "s/\${HAPROXY_STATS_USER}/${HAPROXY_STATS_USER}/g" \
    -e "s/\${HAPROXY_STATS_PASSWORD}/${HAPROXY_STATS_PASSWORD}/g" \
    -e "s/\${HAPROXY_API_GATEWAY_PORT}/${HAPROXY_API_GATEWAY_PORT}/g" \
    -e "s/\${HAPROXY_FASTAPI_BACKEND}/${HAPROXY_FASTAPI_BACKEND}/g" \
    -e "s/\${HAPROXY_MINIO_BACKEND}/${HAPROXY_MINIO_BACKEND}/g" \
    /usr/local/etc/haproxy/haproxy.cfg.template > /tmp/haproxy.cfg

exec haproxy -f /tmp/haproxy.cfg
