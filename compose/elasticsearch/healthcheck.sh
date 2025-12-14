#!/bin/bash

curl -f -u elastic:$ELASTIC_PASSWORD http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s || exit 1
