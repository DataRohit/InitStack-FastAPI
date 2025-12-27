#!/bin/sh

wget --quiet --tries=1 --timeout=5 --spider http://localhost:9090/-/healthy || exit 1
