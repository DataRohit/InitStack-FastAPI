#!/bin/bash

set -e

if [ ! -f /var/lib/rabbitmq/.erlang.cookie ]; then
    echo "Zx4vB9nK2mQ8wE5r" > /var/lib/rabbitmq/.erlang.cookie
    chmod 600 /var/lib/rabbitmq/.erlang.cookie
    chown rabbitmq:rabbitmq /var/lib/rabbitmq/.erlang.cookie
fi

exec docker-entrypoint.sh rabbitmq-server
