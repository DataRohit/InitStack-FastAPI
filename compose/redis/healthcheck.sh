#!/bin/bash

redis-cli -a "$REDIS_PASSWORD" ping | grep -q "PONG"
