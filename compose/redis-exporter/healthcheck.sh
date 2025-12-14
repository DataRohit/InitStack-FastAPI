#!/bin/sh

wget --no-verbose --tries=1 --spider http://localhost:9121/metrics || exit 1
