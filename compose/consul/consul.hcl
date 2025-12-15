datacenter = "${CONSUL_DATACENTER}"
data_dir = "/consul/data"
log_level = "${CONSUL_LOG_LEVEL}"
log_json = ${CONSUL_LOG_JSON}
enable_syslog = ${CONSUL_ENABLE_SYSLOG}
syslog_facility = "${CONSUL_SYSLOG_FACILITY}"
node_name = "${CONSUL_NODE_NAME}"
bind_addr = "${CONSUL_BIND_ADDR}"
client_addr = "${CONSUL_CLIENT_ADDR}"
retry_join = ["127.0.0.1"]
server = true
bootstrap_expect = ${CONSUL_BOOTSTRAP_EXPECT}
ui_config {
  enabled = ${CONSUL_UI_ENABLED}
}
connect {
  enabled = ${CONSUL_CONNECT_ENABLED}
}
ports {
  grpc = ${CONSUL_PORTS_GRPC}
  grpc_tls = ${CONSUL_PORTS_GRPC_TLS}
  http = ${CONSUL_HTTP_PORT}
  dns = ${CONSUL_DNS_PORT}
  serf_lan = ${CONSUL_SERF_LAN_PORT}
  serf_wan = ${CONSUL_SERF_WAN_PORT}
  server = ${CONSUL_SERVER_PORT}
}
acl = {
  enabled = ${CONSUL_ACL_ENABLED}
  default_policy = "${CONSUL_ACL_DEFAULT_POLICY}"
  enable_token_persistence = ${CONSUL_ACL_ENABLE_TOKEN_PERSISTENCE}
  tokens = {
    initial_management = "${CONSUL_ACL_MASTER_TOKEN}"
    agent = "${CONSUL_ACL_AGENT_TOKEN}"
    agent_recovery = "${CONSUL_ACL_AGENT_MASTER_TOKEN}"
  }
}
encrypt = "${CONSUL_ENCRYPT_KEY}"
disable_host_node_id = ${CONSUL_DISABLE_HOST_NODE_ID}
disable_update_check = ${CONSUL_DISABLE_UPDATE_CHECK}
enable_script_checks = ${CONSUL_ENABLE_SCRIPT_CHECKS}
enable_local_script_checks = ${CONSUL_ENABLE_LOCAL_SCRIPT_CHECKS}
leave_on_terminate = ${CONSUL_LEAVE_ON_TERMINATE}
skip_leave_on_interrupt = ${CONSUL_SKIP_LEAVE_ON_INTERRUPT}
rejoin_after_leave = ${CONSUL_REJOIN_AFTER_LEAVE}
enable_debug = ${CONSUL_ENABLE_DEBUG}
disable_anonymous_signature = ${CONSUL_DISABLE_ANONYMOUS_SIGNATURE}
disable_remote_exec = ${CONSUL_DISABLE_REMOTE_EXEC}
performance {
  raft_multiplier = ${CONSUL_PERFORMANCE_RAFT_MULTIPLIER}
}
telemetry {
  prometheus_retention_time = "${CONSUL_TELEMETRY_PROMETHEUS_RETENTION_TIME}"
  disable_hostname = ${CONSUL_TELEMETRY_DISABLE_HOSTNAME}
}
autopilot {
  cleanup_dead_servers = ${CONSUL_AUTOPILOT_CLEANUP_DEAD_SERVERS}
  last_contact_threshold = "${CONSUL_AUTOPILOT_LAST_CONTACT_THRESHOLD}"
  max_trailing_logs = ${CONSUL_AUTOPILOT_MAX_TRAILING_LOGS}
  server_stabilization_time = "${CONSUL_AUTOPILOT_SERVER_STABILIZATION_TIME}"
  disable_upgrade_migration = ${CONSUL_AUTOPILOT_DISABLE_UPGRADE_MIGRATION}
}
