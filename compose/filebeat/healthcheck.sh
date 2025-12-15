#!/bin/bash

set -e

curl -f -s http://localhost:5066/stats || exit 1
