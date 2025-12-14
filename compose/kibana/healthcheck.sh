#!/bin/bash

curl -f http://localhost:5601/api/status || exit 1
