import json
import re
from re import Match
from typing import Any
from typing import LiteralString

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings


def _parse_expiry_to_seconds(*, v: Any, env_name: str) -> Any:
    """Parse Expiry From Env Input.

    Arguments:
        v (Any): Raw environment value.
        env_name (str): Environment variable name for error messages.

    Returns:
        Any: Parsed integer seconds.

    Raises:
        ValueError: If expiry format is invalid.
    """

    if isinstance(v, int):
        return v

    if isinstance(v, str):
        raw: str = v.strip()
        if raw.isdigit():
            return int(raw)

        parts: list[str] = [part.strip() for part in raw.split("/") if part.strip()]
        if not parts:
            msg = f"Invalid {env_name} format. Use integer seconds or duration like 15m"
            raise ValueError(msg)

        def parse_part(part: str) -> int:
            match: Match[str] | None = re.fullmatch(pattern=r"(?i)(\d+)\s*([smhd])", string=part)
            if match is None:
                msg = f"Invalid {env_name} format. Use integer seconds or duration like 15m"
                raise ValueError(msg)

            amount: int = int(match.group(1))
            unit: str = match.group(2).lower()
            multipliers: dict[str, int] = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            return amount * multipliers[unit]

        primary: int = parse_part(part=parts[0])
        if len(parts) > 1:
            secondary: int = parse_part(part=parts[1])
            if secondary != primary:
                msg = f"Invalid {env_name} format. Duration parts must match (e.g. 1d/24h)"
                raise ValueError(msg)

        return primary
    return v


class Settings(BaseSettings):
    """Application Settings For InitStack FastAPI Server.

    Inherits:
        BaseSettings

    Attributes:
        app_name (str): Application name.
        app_version (str): Application version.
        app_description (str): Application description.
        app_contact_name (str): Contact name.
        app_contact_email (str): Contact email.
        app_license_name (str): License name.
        app_license_url (str): License URL.
        api_base_url (str): Base URL for API endpoints.
        debug (bool): Enable debug mode.
        environment (str): Runtime environment name.
        host (str): Host interface to bind.
        port (int): Port to bind.
        reload (bool): Enable auto-reload.
        cors_origins (list[str]): Allowed CORS origins.
        cors_allow_credentials (bool): Allow CORS credentials.
        cors_allow_methods (list[str]): Allowed CORS methods.
        cors_allow_headers (list[str]): Allowed CORS headers.
        log_level (str): Logging level.
        log_format (str): Logging format.
        workers (int): Number of server workers.
        proxy_headers_enabled (bool): Enable proxy headers middleware.
        proxy_headers_trusted_hosts (list[str]): Trusted hosts for proxy headers.
        max_request_size (int): Maximum request body size in bytes.
        max_upload_size (int): Maximum upload file size in bytes.
        consul_enabled (bool): Enable Consul service discovery.
        consul_host (str): Consul server host.
        consul_port (int): Consul server port.
        consul_token (str): Consul ACL token.
        consul_datacenter (str): Consul datacenter.
        consul_scheme (str): Consul connection scheme.
        consul_verify (bool): Verify SSL certificates.
        consul_service_name (str): Service name for Consul registration.
        consul_service_tags (list[str]): Service tags for Consul registration.
        consul_health_check_interval (str): Health check interval.
        consul_health_check_timeout (str): Health check timeout.
        consul_health_check_deregister_critical_after (str): Deregister after critical.
        redis_enabled (bool): Enable Redis connection.
        redis_host (str): Redis server host.
        redis_port (int): Redis server port.
        redis_username (str): Redis username.
        redis_password (str): Redis password.
        redis_database (int): Redis database number.
        redis_token_cache_db (int): Redis database number used for token caching.
        redis_ssl (bool): Enable SSL for Redis connection.
        redis_ssl_verify (bool): Verify SSL certificates for Redis.
        redis_connection_timeout (int): Redis connection timeout in seconds.
        redis_socket_timeout (int): Redis socket timeout in seconds.
        redis_socket_keepalive (bool): Enable Redis socket keepalive.
        redis_socket_keepalive_options (dict[str, Any]): Redis socket keepalive options.
        redis_health_check_interval (int): Redis health check interval in seconds.
        redis_max_connections (int): Maximum Redis connections in pool.
        redis_retry_on_timeout (bool): Retry Redis operations on timeout.
        redis_decode_responses (bool): Decode Redis responses to strings.
        redis_encoding (str): Redis response encoding.
        rate_limit_enabled (bool): Enable rate limiting middleware.
        rate_limit_requests_per_minute (int): Maximum requests per minute per client.
        rate_limit_burst_size (int): Burst size for rate limiting.
        rate_limit_window_size (int): Rate limit window size in seconds.
        rate_limit_redis_key_prefix (str): Redis key prefix for rate limiting.
        rate_limit_redis_key_expiry (int): Redis key expiry for rate limiting in seconds.
        rate_limit_exempt_ips (list[str]): IP addresses exempt from rate limiting.
        rate_limit_header_enabled (bool): Include rate limit headers in responses.
        rate_limit_retry_after_header (bool): Include Retry-After header when rate limited.
        telemetry_enabled (bool): Enable OpenTelemetry export.
        telemetry_service_name (str): Telemetry service name override.
        telemetry_endpoint (str): OTLP endpoint for traces and metrics.
        telemetry_timeout (int): Telemetry exporter timeout in seconds.
        telemetry_headers (dict[str, Any]): Additional OTLP request headers.
        telemetry_metrics_interval (int): Metrics export interval in seconds.
        otel_metrics_enabled (bool): Enable OpenTelemetry metrics collection.
        otel_service_name (str): Service name for OpenTelemetry metrics.
        otel_metrics_export_interval (int): Metrics collection interval in milliseconds.
        otel_resource_attributes (dict[str, Any]): Custom resource attributes for metrics.
        otel_prometheus_endpoint (str): Prometheus endpoint path for metrics scraping.
        rabbitmq_enabled (bool): Enable RabbitMQ connection.
        rabbitmq_host (str): RabbitMQ server host.
        rabbitmq_port (int): RabbitMQ server port.
        rabbitmq_username (str): RabbitMQ username.
        rabbitmq_password (str): RabbitMQ password.
        rabbitmq_vhost (str): RabbitMQ virtual host.
        rabbitmq_ssl (bool): Enable SSL for RabbitMQ connection.
        rabbitmq_ssl_verify (bool): Verify SSL certificates for RabbitMQ.
        rabbitmq_connection_timeout (int): RabbitMQ connection timeout in seconds.
        rabbitmq_heartbeat (int): RabbitMQ heartbeat interval in seconds.
        rabbitmq_blocked_connection_timeout (int): RabbitMQ blocked connection timeout in seconds.
        rabbitmq_max_channels (int): Maximum RabbitMQ channels per connection.
        rabbitmq_prefetch_count (int): RabbitMQ prefetch count for consumers.
        rabbitmq_connection_name (str): RabbitMQ connection name.
        elasticsearch_enabled (bool): Enable Elasticsearch connection.
        elasticsearch_hosts (list[str]): Elasticsearch server hosts.
        elasticsearch_username (str): Elasticsearch username.
        elasticsearch_password (str): Elasticsearch password.
        elasticsearch_ssl (bool): Enable SSL for Elasticsearch connection.
        elasticsearch_ssl_verify (bool): Verify SSL certificates for Elasticsearch.
        elasticsearch_connection_timeout (int): Elasticsearch connection timeout in seconds.
        elasticsearch_request_timeout (int): Elasticsearch request timeout in seconds.
        elasticsearch_max_retries (int): Maximum Elasticsearch retry attempts.
        elasticsearch_retry_on_timeout (bool): Retry Elasticsearch requests on timeout.
        smtp_enabled (bool): Enable SMTP mail transport.
        smtp_host (str): SMTP server host.
        smtp_port (int): SMTP server port.
        smtp_username (str): SMTP username.
        smtp_password (str): SMTP password.
        smtp_use_tls (bool): Use TLS for SMTP connection.
        smtp_use_ssl (bool): Use SSL for SMTP connection.
        smtp_timeout (int): SMTP connection timeout in seconds.
        smtp_from_email (str): Default sender email address.
        smtp_from_name (str): Default sender display name.
        minio_enabled (bool): Enable MinIO object storage.
        minio_endpoint (str): MinIO server endpoint.
        minio_access_key (str): MinIO access key.
        minio_secret_key (str): MinIO secret key.
        minio_bucket_name (str): MinIO bucket name.
        minio_secure (bool): Use secure (HTTPS) connection to MinIO.
        minio_region (str): MinIO bucket region.
        celery_broker_url (str): Celery broker connection URL.
        celery_result_backend (str): Celery result backend URL.
        celery_worker_name (str): Celery worker name.
        celery_worker_concurrency (int): Number of concurrent worker processes.
        celery_worker_prefetch_multiplier (int): Worker prefetch multiplier.
        celery_worker_max_tasks_per_child (int): Maximum tasks per worker child process.
        celery_worker_log_level (str): Worker logging level.
        celery_task_serializer (str): Task serialization format.
        celery_result_serializer (str): Result serialization format.
        celery_accept_content (list[str]): Accepted content types.
        celery_timezone (str): Celery timezone.
        celery_enable_utc (bool): Enable UTC timezone.
        celery_task_track_started (bool): Track when tasks start.
        celery_task_time_limit (int): Hard task time limit in seconds.
        celery_task_soft_time_limit (int): Soft task time limit in seconds.
        celery_task_acks_late (bool): Acknowledge tasks after completion.
        celery_task_reject_on_worker_lost (bool): Reject tasks on worker loss.
        celery_result_expires (int): Result expiration time in seconds.
        celery_result_persistent (bool): Persist results.
        celery_result_compression (str): Result compression algorithm.
        celery_broker_connection_retry (bool): Retry broker connections.
        celery_broker_connection_retry_on_startup (bool): Retry connections on startup.
        celery_broker_connection_max_retries (int): Maximum connection retry attempts.
        celery_elasticsearch_index_prefix (str): Elasticsearch index prefix for results.
        celery_elasticsearch_doc_type (str): Elasticsearch document type.
        celery_beat_scheduler (str): Beat scheduler class.
        celery_beat_schedule_filename (str): Beat schedule file path.
        celery_beat_log_level (str): Beat scheduler logging level.
        celery_flower_port (int): Flower monitoring port.
        celery_flower_address (str): Flower bind address.
        celery_flower_log_level (str): Flower logging level.
        celery_flower_basic_auth (str): Flower basic authentication credentials.
        celery_flower_url_prefix (str): Flower URL prefix.
        celery_flower_max_tasks (int): Maximum tasks to display in Flower.
        celery_flower_persistent (bool): Enable Flower persistence.
        celery_flower_db (str): Flower database file path.
        celery_flower_enable_events (bool): Enable Celery events in Flower.
        celery_flower_auto_refresh (bool): Enable auto-refresh in Flower.
        celery_flower_refresh_interval (int): Flower refresh interval in milliseconds.
        postgresql_enabled (bool): Enable PostgreSQL connection.
        postgresql_host (str): PostgreSQL server host.
        postgresql_port (int): PostgreSQL server port.
        postgresql_username (str): PostgreSQL username.
        postgresql_password (str): PostgreSQL password.
        postgresql_database (str): PostgreSQL database name.
        postgresql_pool_size (int): PostgreSQL connection pool size.
        postgresql_max_overflow (int): Maximum overflow connections in pool.
        postgresql_pool_timeout (int): Connection pool timeout in seconds.
        postgresql_pool_recycle (int): Connection recycle time in seconds.
        postgresql_pool_pre_ping (bool): Enable connection pre-ping.
        postgresql_echo (bool): Enable SQL statement logging.
        postgresql_echo_pool (bool): Enable connection pool logging.
        postgresql_ssl_mode (str): PostgreSQL SSL mode.
        signup_token_secret (str): Secret key used to sign signup tokens.
        signup_token_expiry_seconds (int): Signup token expiry time in seconds.
        forgot_password_token_secret (str): Secret key used to sign forgot password tokens.
        forgot_password_token_expiry_seconds (int): Forgot password token expiry time in seconds.
        reset_password_token_secret (str): Secret key used to sign reset password tokens.
        reset_password_token_expiry_seconds (int): Reset password token expiry time in seconds.
        access_token_secret (str): Secret key used to sign access tokens.
        access_token_expiry_seconds (int): Access token expiry time in seconds.
        refresh_token_secret (str): Secret key used to sign refresh tokens.
        refresh_token_expiry_seconds (int): Refresh token expiry time in seconds.
        deactivate_token_secret (str): Secret key used to sign deactivate tokens.
        deactivate_token_expiry_seconds (int): Deactivate token expiry time in seconds.
        reactivate_token_secret (str): Secret key used to sign reactivate tokens.
        reactivate_token_expiry_seconds (int): Reactivate token expiry time in seconds.
        oauth_google_client_id (str): Google OAuth client ID.
        oauth_google_client_secret (str): Google OAuth client secret.
        oauth_github_client_id (str): GitHub OAuth client ID.
        oauth_github_client_secret (str): GitHub OAuth client secret.
        oauth_session_secret (str): Secret key for OAuth session middleware.
        oauth_redirect_base_url (str | None): Base URL for OAuth callbacks.

    Properties:
        None

    Methods:
        parse_cors_origins: Parse CORS origins from env input.
        parse_cors_methods: Parse CORS methods from env input.
        parse_cors_headers: Parse CORS headers from env input.
        parse_proxy_headers_trusted_hosts: Parse proxy headers trusted hosts from env input.
        parse_consul_service_tags: Parse Consul service tags from env input.
        parse_redis_socket_keepalive_options: Parse Redis socket keepalive options from env input.
        parse_rate_limit_exempt_ips: Parse rate limit exempt IPs from env input.
        parse_telemetry_headers: Parse telemetry headers from env input.
        parse_signup_token_expiry_seconds: Parse signup token expiry from env input.
        parse_forgot_password_token_expiry_seconds: Parse forgot password token expiry from env input.
        parse_reset_password_token_expiry_seconds: Parse reset password token expiry from env input.
        parse_access_token_expiry_seconds: Parse access token expiry from env input.
        parse_refresh_token_expiry_seconds: Parse refresh token expiry from env input.
        parse_deactivate_token_expiry_seconds: Parse deactivate token expiry from env input.
        parse_reactivate_token_expiry_seconds: Parse reactivate token expiry from env input.
    """

    app_name: str = "InitStack FastAPI Development Server"
    app_version: str = "0.1.0"
    app_description: str = "Professional FastAPI Server For Development."
    app_contact_name: str = "Rohit Vilas Ingole"
    app_contact_email: str = "rohit.vilas.ingole@gmail.com"
    app_license_name: str = "MIT"
    app_license_url: str = "https://github.com/DataRohit/InitStack/blob/master/license"

    api_base_url: str = "http://localhost:8000"

    debug: bool = True
    environment: str = "development"

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8080
    reload: bool = True

    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    )
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    log_level: str = "DEBUG"
    log_format: str = "json"

    workers: int = 1

    proxy_headers_enabled: bool = True
    proxy_headers_trusted_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
    )

    max_request_size: int = 16777216
    max_upload_size: int = 104857600

    consul_enabled: bool = True
    consul_host: str = "initstack-consul-service"
    consul_port: int = 8500
    consul_token: str = "Mx7nQ4wR8vK2sL9p"  # noqa: S105
    consul_datacenter: str = "dc1"
    consul_scheme: str = "http"
    consul_verify: bool = True
    consul_service_name: str = "initstack-fastapi-service"
    consul_service_tags: list[str] = Field(default_factory=lambda: ["fastapi", "api", "web"])
    consul_health_check_interval: str = "30s"
    consul_health_check_timeout: str = "10s"
    consul_health_check_deregister_critical_after: str = "90s"

    redis_enabled: bool = True
    redis_host: str = "initstack-redis-service"
    redis_port: int = 6379
    redis_username: str = "z2yju1mD0GQxgV6Z"
    redis_password: str = "Bv3cX8nM1qW6eR9t"  # noqa: S105
    redis_database: int = 0
    redis_token_cache_db: int = 1
    redis_ssl: bool = False
    redis_ssl_verify: bool = True
    redis_connection_timeout: int = 5
    redis_socket_timeout: int = 5
    redis_socket_keepalive: bool = True
    redis_socket_keepalive_options: dict[str, Any] = Field(default_factory=dict)
    redis_health_check_interval: int = 30
    redis_max_connections: int = 50
    redis_retry_on_timeout: bool = True
    redis_decode_responses: bool = True
    redis_encoding: str = "utf-8"

    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 120
    rate_limit_burst_size: int = 20
    rate_limit_window_size: int = 60
    rate_limit_redis_key_prefix: str = "rate_limit"
    rate_limit_redis_key_expiry: int = 3600
    rate_limit_exempt_ips: list[str] = Field(default_factory=list)
    rate_limit_header_enabled: bool = True
    rate_limit_retry_after_header: bool = True

    telemetry_enabled: bool = True
    telemetry_service_name: str = "initstack-fastapi-service"
    telemetry_endpoint: str = "http://initstack-apm-service:8200"
    telemetry_timeout: int = 10
    telemetry_headers: dict[str, Any] = Field(default_factory=dict)
    telemetry_metrics_interval: int = 30

    otel_metrics_enabled: bool = True
    otel_service_name: str = "initstack-fastapi-service"
    otel_metrics_export_interval: int = 5000
    otel_resource_attributes: dict[str, Any] = Field(default_factory=dict)
    otel_prometheus_endpoint: str = "/api/v1/telemetry/health"

    rabbitmq_enabled: bool = True
    rabbitmq_host: str = "initstack-rabbitmq-service"
    rabbitmq_port: int = 5672
    rabbitmq_username: str = "Qw8rT5nM3xZ9pL2v"
    rabbitmq_password: str = "Hj6kN4mB8vC1sF7q"  # noqa: S105
    rabbitmq_vhost: str = "initstack_vhost"
    rabbitmq_ssl: bool = False
    rabbitmq_ssl_verify: bool = True
    rabbitmq_connection_timeout: int = 10
    rabbitmq_heartbeat: int = 30
    rabbitmq_blocked_connection_timeout: int = 300
    rabbitmq_max_channels: int = 2047
    rabbitmq_prefetch_count: int = 10
    rabbitmq_connection_name: str = "initstack-fastapi-service"

    elasticsearch_enabled: bool = True
    elasticsearch_hosts: list[str] = Field(default_factory=lambda: ["http://initstack-elasticsearch-service:9200"])
    elasticsearch_username: str = "elastic"
    elasticsearch_password: str = "Mx7nQ4wR8vK2sL9p"  # noqa: S105
    elasticsearch_ssl: bool = False
    elasticsearch_ssl_verify: bool = True
    elasticsearch_connection_timeout: int = 10
    elasticsearch_request_timeout: int = 30
    elasticsearch_max_retries: int = 3
    elasticsearch_retry_on_timeout: bool = True

    smtp_enabled: bool = True
    smtp_host: str = "initstack-mailpit-service"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    smtp_timeout: int = 10
    smtp_from_email: str = "noreply@initstack.local"
    smtp_from_name: str = "InitStack"

    minio_enabled: bool = True
    minio_endpoint: str = "initstack-minio-service:9000"
    minio_access_key: str = "qHxw14DQ1zVmO80H4AFj"
    minio_secret_key: str = "38dw8Dh6x5c0kO3DjVGZMlioi6EGnMgR89UH0Tko"  # noqa: S105
    minio_bucket_name: str = "initstack"
    minio_secure: bool = False
    minio_region: str = "us-east-1"

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_worker_name: str = "initstack-celery-worker"
    celery_worker_concurrency: int = 4
    celery_worker_prefetch_multiplier: int = 4
    celery_worker_max_tasks_per_child: int = 1000
    celery_worker_log_level: str = "INFO"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list[str] = Field(default_factory=lambda: ["json"])
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 3600
    celery_task_soft_time_limit: int = 3000
    celery_task_acks_late: bool = True
    celery_task_reject_on_worker_lost: bool = True
    celery_result_expires: int = 86400
    celery_result_persistent: bool = True
    celery_result_compression: str = "gzip"
    celery_broker_connection_retry: bool = True
    celery_broker_connection_retry_on_startup: bool = True
    celery_broker_connection_max_retries: int = 10
    celery_elasticsearch_index_prefix: str = "celery"
    celery_elasticsearch_doc_type: str = "_doc"
    celery_beat_scheduler: str = "celery.beat:PersistentScheduler"
    celery_beat_schedule_filename: str = "/var/lib/celery/celerybeat-schedule"
    celery_beat_log_level: str = "INFO"
    celery_flower_port: int = 5555
    celery_flower_address: str = "0.0.0.0"  # noqa: S104
    celery_flower_log_level: str = "INFO"
    celery_flower_basic_auth: str = "admin:Zx7kP9mN3qW8rT5yHj2vB6nC4sF1dG8a"
    celery_flower_url_prefix: str = ""
    celery_flower_max_tasks: int = 10000
    celery_flower_persistent: bool = True
    celery_flower_db: str = "/var/lib/flower/flower.db"
    celery_flower_enable_events: bool = True
    celery_flower_auto_refresh: bool = True
    celery_flower_refresh_interval: int = 5000

    postgresql_enabled: bool = True
    postgresql_host: str = "initstack-postgresql-service"
    postgresql_port: int = 5432
    postgresql_username: str = "G4qoziOrpaVsfa8A"
    postgresql_password: str = "Kx9mP2nQ7wR5tY8uVb3cX8nM1qW6eR9t"  # noqa: S105
    postgresql_database: str = "initstack_db"
    postgresql_pool_size: int = 20
    postgresql_max_overflow: int = 10
    postgresql_pool_timeout: int = 30
    postgresql_pool_recycle: int = 3600
    postgresql_pool_pre_ping: bool = True
    postgresql_echo: bool = False
    postgresql_echo_pool: bool = False
    postgresql_ssl_mode: str = "disable"

    signup_token_secret: str = "7560c27c873f5fd102a79b56b25a6207"  # noqa: S105
    signup_token_expiry_seconds: int = Field(default=900, validation_alias="SIGNUP_TOKEN_EXPIRY")

    forgot_password_token_secret: str = "740921661bb9838170c8fd109e69151f"  # noqa: S105
    forgot_password_token_expiry_seconds: int = Field(default=900, validation_alias="FORGOT_PASSWORD_TOKEN_EXPIRY")

    reset_password_token_secret: str = "365bcd17a4563a363e0f4af7517b4f73"  # noqa: S105
    reset_password_token_expiry_seconds: int = Field(default=900, validation_alias="RESET_PASSWORD_TOKEN_EXPIRY")

    access_token_secret: str = "a92218dbd59bef1e2501877958d22103"  # noqa: S105
    access_token_expiry_seconds: int = Field(default=1800, validation_alias="ACCESS_TOKEN_EXPIRY")

    refresh_token_secret: str = "794dbdfbec0f3421d796f7fd2e620e5f"  # noqa: S105
    refresh_token_expiry_seconds: int = Field(default=86400, validation_alias="REFRESH_TOKEN_EXPIRY")

    deactivate_token_secret: str = "c4f8e2a1b9d6f3e7a5c2b8d4f1e9a6c3"  # noqa: S105
    deactivate_token_expiry_seconds: int = Field(default=900, validation_alias="DEACTIVATE_TOKEN_EXPIRY")

    reactivate_token_secret: str = "b7e3d9f2c5a8e1d4b6f9c2a7e4d1b8f5"  # noqa: S105
    reactivate_token_expiry_seconds: int = Field(default=900, validation_alias="REACTIVATE_TOKEN_EXPIRY")

    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    oauth_github_client_id: str = ""
    oauth_github_client_secret: str = ""
    oauth_session_secret: str = "d8f3e9a2c7b4f1e6d9c3a8f5b2e7d4a1"  # noqa: S105
    oauth_redirect_base_url: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        """Parse CORS Origins From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a list of strings.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v: Any) -> Any:
        """Parse CORS Methods From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a list of strings.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return [method.strip() for method in v.split(",")]
        return v

    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v: Any) -> Any:
        """Parse CORS Headers From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a list of strings.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return [header.strip() for header in v.split(",")]
        return v

    @field_validator("proxy_headers_trusted_hosts", mode="before")
    @classmethod
    def parse_proxy_headers_trusted_hosts(cls, v: Any) -> Any:
        """Parse Proxy Headers Trusted Hosts From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a list of strings.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return [host.strip() for host in v.split(",")]
        return v

    @field_validator("consul_service_tags", mode="before")
    @classmethod
    def parse_consul_service_tags(cls, v: Any) -> Any:
        """Parse Consul Service Tags From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a list of strings.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return [tag.strip() for tag in v.split(",")]
        return v

    @field_validator("redis_socket_keepalive_options", mode="before")
    @classmethod
    def parse_redis_socket_keepalive_options(cls, v: Any) -> Any:
        """Parse Redis Socket Keepalive Options From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a dictionary.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return {}
        return v

    @field_validator("rate_limit_exempt_ips", mode="before")
    @classmethod
    def parse_rate_limit_exempt_ips(cls, v: Any) -> Any:
        """Parse Rate Limit Exempt IPs From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a list of strings.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return [ip.strip() for ip in v.split(",")]
        return v

    @field_validator("telemetry_headers", mode="before")
    @classmethod
    def parse_telemetry_headers(cls, v: Any) -> Any:
        """Parse Telemetry Headers From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a dictionary.

        Raises:
            None
        """

        if isinstance(v, str):
            try:
                return json.loads(s=v)
            except json.JSONDecodeError:
                return {}
        return v

    # Parse Otel Resource Attributes Function
    @field_validator("otel_resource_attributes", mode="before")
    @classmethod
    def parse_otel_resource_attributes(cls, v: Any) -> Any:
        """Parse Otel Resource Attributes From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed value, typically a dictionary.

        Raises:
            None
        """

        # Check If String
        if isinstance(v, str):
            try:
                # Parse JSON
                return json.loads(s=v)

            except json.JSONDecodeError:
                # Return Empty Dict
                return {}

        # Return Value
        return v

    class Config:
        """Pydantic Settings Configuration For Environment Loading.

        Inherits:
            object

        Attributes:
            case_sensitive (bool): Whether environment variable names are case-sensitive.

        Properties:
            None

        Methods:
            None
        """

        case_sensitive: bool = False

    @field_validator("signup_token_expiry_seconds", mode="before")
    @classmethod
    def parse_signup_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Signup Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="SIGNUP_TOKEN_EXPIRY")

    @field_validator("forgot_password_token_expiry_seconds", mode="before")
    @classmethod
    def parse_forgot_password_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Forgot Password Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="FORGOT_PASSWORD_TOKEN_EXPIRY")

    @field_validator("reset_password_token_expiry_seconds", mode="before")
    @classmethod
    def parse_reset_password_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Reset Password Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="RESET_PASSWORD_TOKEN_EXPIRY")

    @field_validator("access_token_expiry_seconds", mode="before")
    @classmethod
    def parse_access_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Access Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="ACCESS_TOKEN_EXPIRY")

    @field_validator("refresh_token_expiry_seconds", mode="before")
    @classmethod
    def parse_refresh_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Refresh Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="REFRESH_TOKEN_EXPIRY")

    @field_validator("deactivate_token_expiry_seconds", mode="before")
    @classmethod
    def parse_deactivate_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Deactivate Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="DEACTIVATE_TOKEN_EXPIRY")

    @field_validator("reactivate_token_expiry_seconds", mode="before")
    @classmethod
    def parse_reactivate_token_expiry_seconds(cls, v: Any) -> Any:
        """Parse Reactivate Token Expiry From Env Input.

        Arguments:
            v (Any): Raw environment value.

        Returns:
            Any: Parsed integer seconds.

        Raises:
            ValueError: If format is invalid.
        """

        return _parse_expiry_to_seconds(v=v, env_name="REACTIVATE_TOKEN_EXPIRY")

    @model_validator(mode="after")
    def construct_celery_urls(self) -> Settings:
        """Construct Celery Broker And Result Backend URLs From Service Settings.

        Arguments:
            None

        Returns:
            Settings: Settings instance with constructed URLs.

        Raises:
            None
        """

        if not self.celery_broker_url:
            self.celery_broker_url = (
                f"amqp://{self.rabbitmq_username}:{self.rabbitmq_password}"
                f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
            )

        if not self.celery_result_backend:
            es_host: LiteralString = (
                self.elasticsearch_hosts[0]
                if self.elasticsearch_hosts
                else "http://initstack-elasticsearch-service:9200"
            )
            es_host_without_scheme: LiteralString = es_host.replace("http://", "").replace("https://", "")
            self.celery_result_backend = (
                f"elasticsearch://{self.elasticsearch_username}:{self.elasticsearch_password}@{es_host_without_scheme}"
            )

        return self


settings: Settings = Settings()


__all__: list[str] = ["Settings", "settings"]
