#!/bin/sh

echo "Waiting For Dependencies To Be Ready..."
sleep 60

echo "Starting Backend Application..."
exec python -m watchfiles "python -m app"
