#!/bin/sh

haproxy -c -f /tmp/haproxy.cfg 2>/dev/null || exit 0
