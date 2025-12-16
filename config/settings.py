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

    Properties:
        None

    Methods:
        parse_cors_origins: Parse CORS origins from env input.
        parse_cors_methods: Parse CORS methods from env input.
        parse_cors_headers: Parse CORS headers from env input.
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
    log_format: str = "standard"

    workers: int = 1

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
