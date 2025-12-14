#!/bin/bash

rabbitmq-diagnostics -q ping && rabbitmq-diagnostics -q check_running
