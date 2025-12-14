#!/bin/bash

set -e

echo "Configuring system settings for SonarQube..."

sysctl -w vm.max_map_count=524288 || echo "Warning: Could not set vm.max_map_count"
sysctl -w fs.file-max=131072 || echo "Warning: Could not set fs.file-max"

echo "System configuration completed"
