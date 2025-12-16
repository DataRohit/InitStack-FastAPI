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

    Properties:
        None

    Methods:
        parse_cors_origins: Parse CORS origins from env input.
        parse_cors_methods: Parse CORS methods from env input.
        parse_cors_headers: Parse CORS headers from env input.
        parse_proxy_headers_trusted_hosts: Parse proxy headers trusted hosts from env input.
        parse_consul_service_tags: Parse Consul service tags from env input.
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
    port: int = 8000
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
