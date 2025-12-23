#!/bin/sh

wget --spider -q http://localhost:8025/api/v1/info || exit 1
