import socket
from typing import TYPE_CHECKING
from typing import Any

from elasticapm.contrib.starlette import ElasticAPM
from elasticapm.contrib.starlette import make_apm_client

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from elasticapm import Client
    from fastapi import FastAPI


def build_apm_config() -> dict[str, Any]:
    """
    Build Elastic APM Configuration Dictionary.

    Arguments:
        None

    Returns:
        dict[str, Any]: Elastic APM configuration dictionary.

    Raises:
        None
    """

    hostname: str = socket.gethostname()

    config: dict[str, Any] = {
        "SERVICE_NAME": settings.telemetry_service_name or settings.app_name,
        "SERVICE_VERSION": settings.app_version,
        "SERVICE_NODE_NAME": f"{settings.telemetry_service_name}-{hostname}",
        "ENVIRONMENT": settings.environment,
        "SERVER_URL": settings.telemetry_endpoint,
        "SECRET_TOKEN": settings.telemetry_headers.get("Authorization", "").replace("Bearer ", ""),
        "VERIFY_SERVER_CERT": False,
        "USE_ELASTIC_TRACEPARENT_HEADER": True,
        "CAPTURE_BODY": "all",
        "CAPTURE_HEADERS": True,
        "TRANSACTION_SAMPLE_RATE": 1.0,
        "TRANSACTION_MAX_SPANS": 500,
        "SPAN_FRAMES_MIN_DURATION": "5ms",
        "STACK_TRACE_LIMIT": 50,
        "COLLECT_LOCAL_VARIABLES": "all",
        "SOURCE_LINES_ERROR_APP_FRAMES": 5,
        "SOURCE_LINES_ERROR_LIBRARY_FRAMES": 5,
        "SOURCE_LINES_SPAN_APP_FRAMES": 5,
        "SOURCE_LINES_SPAN_LIBRARY_FRAMES": 0,
        "LOCAL_VAR_MAX_LENGTH": 200,
        "LOCAL_VAR_LIST_MAX_LENGTH": 10,
        "CAPTURE_ELASTICSEARCH_QUERIES": True,
        "METRICS_INTERVAL": f"{settings.telemetry_metrics_interval}s",
        "DISABLE_METRICS": [],
        "BREAKDOWN_METRICS": True,
        "CENTRAL_CONFIG": False,
        "LOG_LEVEL": "debug" if settings.debug else "info",
        "LOG_FILE": None,
        "LOG_FILE_SIZE": "10mb",
        "FILTER_EXCEPTION_TYPES": [],
        "TRANSACTIONS_IGNORE_PATTERNS": [],
        "SANITIZE_FIELD_NAMES": [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "access_token",
            "auth",
            "credentials",
            "mysql_pwd",
            "stripetoken",
        ],
        "INCLUDE_PATHS": [],
        "EXCLUDE_PATHS": [
            "*/site-packages/*",
            "*/dist-packages/*",
        ],
        "DEBUG": settings.debug,
        "ENABLED": settings.telemetry_enabled,
        "RECORDING": settings.telemetry_enabled,
        "INSTRUMENT": True,
        "VERIFY_CERTIFICATE_PATH": None,
        "SERVER_TIMEOUT": f"{settings.telemetry_timeout}s",
        "HOSTNAME": hostname,
        "AUTO_LOG_STACKS": True,
        "USE_CERTIFI": False,
        "API_REQUEST_TIME": "10s",
        "API_REQUEST_SIZE": "768kb",
        "GLOBAL_LABELS": {
            "service_type": "fastapi",
            "deployment": "docker",
            "stack": "initstack",
            "framework_name": "fastapi",
            "framework_version": "latest",
        },
        "SERVICE_FRAMEWORK_NAME": "FastAPI",
        "SERVICE_FRAMEWORK_VERSION": settings.app_version,
        "SERVICE_LANGUAGE_NAME": "python",
        "PROCESSORS": [
            "elasticapm.processors.sanitize_stacktrace_locals",
            "elasticapm.processors.sanitize_http_request_cookies",
            "elasticapm.processors.sanitize_http_response_cookies",
            "elasticapm.processors.sanitize_http_headers",
            "elasticapm.processors.sanitize_http_wsgi_env",
            "elasticapm.processors.sanitize_http_request_body",
        ],
    }

    return config


def setup_telemetry(app: FastAPI) -> None:
    """
    Configure Elastic APM Tracing And Metrics For FastAPI.

    Arguments:
        app (FastAPI): FastAPI application instance.

    Returns:
        None

    Raises:
        None
    """

    logger: logging.Logger = get_logger(name="telemetry.setup")

    if not settings.telemetry_enabled:
        logger.info(msg="Telemetry disabled")

        return

    try:
        apm_config: dict[str, Any] = build_apm_config()
        apm_client: Client = make_apm_client(config=apm_config)
        app.add_middleware(middleware_class=ElasticAPM, client=apm_client)  # ty:ignore[invalid-argument-type]

        logger.info(
            msg="Elastic APM middleware added successfully",
            extra={
                "apm_server_url": settings.telemetry_endpoint,
                "service_name": settings.telemetry_service_name or settings.app_name,
                "service_version": settings.app_version,
                "environment": settings.environment,
            },
        )

    except Exception as e:
        logger.exception(msg=f"Failed to initialize Elastic APM: {e!s}")


__all__: list[str] = ["build_apm_config", "setup_telemetry"]
