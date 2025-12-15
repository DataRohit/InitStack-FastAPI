#!/bin/sh

set -e

wget -q --spider http://localhost:9187/metrics || exit 1
