#!/bin/bash

curl -f http://localhost:${FLOWER_PORT}/healthcheck > /dev/null 2>&1
