import json
from typing import Any

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings


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
    """

    app_name: str = "InitStack FastAPI Development Server"
    app_version: str = "0.1.0"
    app_description: str = "Professional FastAPI Server For Development."
    app_contact_name: str = "Rohit Vilas Ingole"
    app_contact_email: str = "rohit.vilas.ingole@gmail.com"
    app_license_name: str = "MIT"
    app_license_url: str = "https://github.com/DataRohit/InitStack/blob/master/license"

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
    consul_health_check_interval: str = "10s"
    consul_health_check_timeout: str = "5s"
    consul_health_check_deregister_critical_after: str = "30s"

    redis_enabled: bool = True
    redis_host: str = "initstack-redis-service"
    redis_port: int = 6379
    redis_username: str = "z2yju1mD0GQxgV6Z"
    redis_password: str = "Bv3cX8nM1qW6eR9t"  # noqa: S105
    redis_database: int = 0
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
    rate_limit_requests_per_minute: int = 20
    rate_limit_burst_size: int = 10
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


settings: Settings = Settings()


__all__: list[str] = ["Settings", "settings"]
