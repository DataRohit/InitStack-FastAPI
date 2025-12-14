#!/bin/bash

set -e

if [ ! -f /data/redis.conf ]; then
    cp /usr/local/etc/redis/redis.conf /data/redis.conf
    chown redis:redis /data/redis.conf
fi

exec redis-server /data/redis.conf
