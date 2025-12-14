#!/bin/bash

set -e

curl -f http://localhost:9000/api/system/status | grep -q '"status":"UP"' || exit 1
