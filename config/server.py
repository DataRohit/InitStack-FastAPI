from contextlib import asynccontextmanager
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from config.adapters import ConsulAdapter
from config.adapters import ElasticsearchAdapter
from config.adapters import EmailAdapter
from config.adapters import MinIOAdapter
from config.adapters import PostgreSQLAdapter
from config.adapters import RabbitMQAdapter
from config.adapters import RedisAdapter
from config.adapters import TokenCacheRedisAdapter
from config.adapters import initialize_consul
from config.adapters import initialize_elasticsearch
from config.adapters import initialize_email
from config.adapters import initialize_minio
from config.adapters import initialize_postgresql
from config.adapters import initialize_rabbitmq
from config.adapters import initialize_redis
from config.adapters import setup_telemetry
from config.adapters import shutdown_consul
from config.adapters import shutdown_elasticsearch
from config.adapters import shutdown_email
from config.adapters import shutdown_minio
from config.adapters import shutdown_postgresql
from config.adapters import shutdown_rabbitmq
from config.adapters import shutdown_redis
from config.logger import LoggerManager
from config.logger import get_logger
from config.middlewares import LoggingMiddleware
from config.middlewares import RateLimitMiddleware
from config.middlewares import RequestSizeLimitMiddleware
from config.routes import create_api_router
from config.settings import settings
from src.schemas import ErrorResponse
from src.schemas import ValidationErrorItem
from src.schemas import ValidationErrorResponse

if TYPE_CHECKING:
    import logging
    from collections.abc import AsyncGenerator

    from starlette.requests import Request


def setup_logging():
    """Configure Application Logging.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """
    LoggerManager.setup_root_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: C901, PLR0912, PLR0915
    """Handle Application Lifespan Events.

    Arguments:
        app (FastAPI): FastAPI application instance.

    Returns:
        AsyncGenerator[None, None]: Async context manager for lifespan events.

    Raises:
        None
    """

    startup_logger: logging.Logger = get_logger(name="server.startup")
    startup_logger.info(msg="Application startup initiated")

    redis_adapter = None
    token_cache_redis_adapter = None
    if settings.redis_enabled:
        startup_logger.info(msg="Initializing Redis connections")
        redis_adapter: RedisAdapter | None
        token_cache_redis_adapter: TokenCacheRedisAdapter | None
        redis_adapter, token_cache_redis_adapter = await initialize_redis()
        if redis_adapter:
            startup_logger.info(
                msg="Base Redis connection established",
                extra={
                    "redis_host": settings.redis_host,
                    "redis_port": settings.redis_port,
                    "redis_database": settings.redis_database,
                },
            )
        else:
            startup_logger.warning(msg="Base Redis connection failed")

        if token_cache_redis_adapter:
            startup_logger.info(
                msg="Token cache Redis connection established",
                extra={
                    "redis_host": settings.redis_host,
                    "redis_port": settings.redis_port,
                    "redis_database": settings.redis_token_cache_db,
                },
            )
        else:
            startup_logger.warning(msg="Token cache Redis connection failed")

    postgresql_adapter = None
    if settings.postgresql_enabled:
        startup_logger.info(msg="Initializing PostgreSQL connection")
        postgresql_adapter: PostgreSQLAdapter | None = await initialize_postgresql()
        if postgresql_adapter:
            startup_logger.info(
                msg="PostgreSQL connection established",
                extra={
                    "postgresql_host": settings.postgresql_host,
                    "postgresql_port": settings.postgresql_port,
                    "postgresql_database": settings.postgresql_database,
                },
            )
        else:
            startup_logger.warning(msg="PostgreSQL connection failed")

    rabbitmq_adapter = None
    if settings.rabbitmq_enabled:
        startup_logger.info(msg="Initializing RabbitMQ connection")
        rabbitmq_adapter: RabbitMQAdapter | None = await initialize_rabbitmq()
        if rabbitmq_adapter:
            startup_logger.info(
                msg="RabbitMQ connection established",
                extra={
                    "rabbitmq_host": settings.rabbitmq_host,
                    "rabbitmq_port": settings.rabbitmq_port,
                    "rabbitmq_vhost": settings.rabbitmq_vhost,
                },
            )
        else:
            startup_logger.warning(msg="RabbitMQ connection failed")

    consul_adapter = None
    if settings.consul_enabled:
        startup_logger.info(msg="Initializing Consul service registration")
        consul_adapter: ConsulAdapter | None = await initialize_consul()
        if consul_adapter:
            startup_logger.info(
                msg="Consul service registration completed",
                extra={
                    "service_id": consul_adapter.service_id,
                    "service_name": consul_adapter.service_name,
                },
            )
        else:
            startup_logger.warning(msg="Consul service registration failed")

    elasticsearch_adapter = None
    if settings.elasticsearch_enabled:
        startup_logger.info(msg="Initializing Elasticsearch connection")
        elasticsearch_adapter: ElasticsearchAdapter | None = await initialize_elasticsearch()
        if elasticsearch_adapter:
            startup_logger.info(
                msg="Elasticsearch connection established",
                extra={
                    "elasticsearch_hosts": settings.elasticsearch_hosts,
                },
            )
        else:
            startup_logger.warning(msg="Elasticsearch connection failed")

    email_adapter = None
    if settings.smtp_enabled:
        startup_logger.info(msg="Initializing Email SMTP connection")
        email_adapter: EmailAdapter | None = await initialize_email()
        if email_adapter:
            startup_logger.info(
                msg="Email SMTP connection established",
                extra={
                    "smtp_host": settings.smtp_host,
                    "smtp_port": settings.smtp_port,
                    "smtp_from_email": settings.smtp_from_email,
                },
            )
        else:
            startup_logger.warning(msg="Email SMTP connection failed")

    minio_adapter = None
    if settings.minio_enabled:
        startup_logger.info(msg="Initializing MinIO connection")
        minio_adapter: MinIOAdapter | None = await initialize_minio()
        if minio_adapter:
            startup_logger.info(
                msg="MinIO connection established",
                extra={
                    "minio_endpoint": settings.minio_endpoint,
                    "minio_bucket": settings.minio_bucket_name,
                },
            )
        else:
            startup_logger.warning(msg="MinIO connection failed")

    startup_logger.info(msg="Application startup completed")

    yield

    shutdown_logger: logging.Logger = get_logger(name="server.shutdown")
    shutdown_logger.info(msg="Application shutdown initiated")

    if settings.consul_enabled:
        shutdown_logger.info(msg="Shutting down Consul service registration")
        await shutdown_consul()
        shutdown_logger.info(msg="Consul service deregistration completed")

    if settings.redis_enabled:
        shutdown_logger.info(msg="Shutting down Redis connection")
        await shutdown_redis()
        shutdown_logger.info(msg="Redis connection closed")

    if settings.postgresql_enabled:
        shutdown_logger.info(msg="Shutting down PostgreSQL connection")
        await shutdown_postgresql()
        shutdown_logger.info(msg="PostgreSQL connection closed")

    if settings.rabbitmq_enabled:
        shutdown_logger.info(msg="Shutting down RabbitMQ connection")
        await shutdown_rabbitmq()
        shutdown_logger.info(msg="RabbitMQ connection closed")

    if settings.elasticsearch_enabled:
        shutdown_logger.info(msg="Shutting down Elasticsearch connection")
        await shutdown_elasticsearch()
        shutdown_logger.info(msg="Elasticsearch connection closed")

    if settings.smtp_enabled:
        shutdown_logger.info(msg="Shutting down Email SMTP connection")
        await shutdown_email()
        shutdown_logger.info(msg="Email SMTP connection closed")

    if settings.minio_enabled:
        shutdown_logger.info(msg="Shutting down MinIO connection")
        await shutdown_minio()
        shutdown_logger.info(msg="MinIO connection closed")

    shutdown_logger.info(msg="Application shutdown completed")


def create_app() -> FastAPI:  # noqa: C901, PLR0915
    """Create And Configure FastAPI Application.

    Arguments:
        None

    Returns:
        FastAPI: Configured FastAPI application instance.

    Raises:
        None
    """

    setup_logging()

    logger: logging.Logger = get_logger(name="server.create_app")
    logger.info(msg="Initializing FastAPI application")

    app: FastAPI = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        contact={
            "name": settings.app_contact_name,
            "email": settings.app_contact_email,
        },
        license_info={
            "name": settings.app_license_name,
            "url": settings.app_license_url,
        },
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    logger.info(msg="Adding logging middleware")
    app.add_middleware(middleware_class=LoggingMiddleware)  # ty:ignore[invalid-argument-type]

    if settings.rate_limit_enabled:
        logger.info(msg="Adding rate limiting middleware")
        app.add_middleware(middleware_class=RateLimitMiddleware)  # ty:ignore[invalid-argument-type]

    logger.info(msg="Adding CORS middleware")
    app.add_middleware(
        middleware_class=CORSMiddleware,  # ty:ignore[invalid-argument-type]
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    if settings.proxy_headers_enabled:
        logger.info(msg="Adding proxy headers middleware")
        app.add_middleware(
            middleware_class=ProxyHeadersMiddleware,  # ty:ignore[invalid-argument-type]
            trusted_hosts=settings.proxy_headers_trusted_hosts,
        )

    logger.info(msg="Adding request size limit middleware")
    app.add_middleware(
        middleware_class=RequestSizeLimitMiddleware,  # ty:ignore[invalid-argument-type]
        max_request_size=settings.max_request_size,
        max_upload_size=settings.max_upload_size,
    )

    if not settings.debug:
        logger.info(msg="Adding trusted host middleware")
        app.add_middleware(
            middleware_class=TrustedHostMiddleware,  # ty:ignore[invalid-argument-type]
            allowed_hosts=["*"],
        )

    if settings.telemetry_enabled:
        logger.info(msg="Initializing telemetry instrumentation")
        setup_telemetry(app=app)

    @app.exception_handler(exc_class_or_status_code=StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP Exceptions.

        Arguments:
            request (Request): Incoming request.
            exc (StarletteHTTPException): Raised HTTP exception.

        Returns:
            JSONResponse: Standardized error response.

        Raises:
            None
        """

        error_logger: logging.Logger = get_logger(name="server.http_exception")
        error_logger.warning(
            msg=f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "url": str(object=request.url),
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.detail,
                detail=f"HTTP {exc.status_code}",
                timestamp=datetime.now(tz=UTC),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(exc_class_or_status_code=RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Request Validation Errors.

        Arguments:
            request (Request): Incoming request.
            exc (RequestValidationError): Validation exception.

        Returns:
            JSONResponse: Standardized validation error response.

        Raises:
            None
        """

        error_logger: logging.Logger = get_logger(name="server.validation_exception")
        error_logger.warning(
            msg=f"Validation error: {exc!s}",
            extra={
                "validation_errors": exc.errors(),
                "url": str(object=request.url),
                "method": request.method,
            },
        )

        def _sanitize_meta(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, (list, tuple)):
                return [_sanitize_meta(value=v) for v in value]
            if isinstance(value, dict):
                return {str(object=k): _sanitize_meta(value=v) for k, v in value.items()}
            return str(object=value)

        errors: list[ValidationErrorItem] = []
        for err in exc.errors():
            loc: Any = err.get("loc")
            if isinstance(loc, (list, tuple)):
                loc_str: str = ".".join(str(object=part) for part in loc)
            else:
                loc_str: str = str(object=loc) if loc is not None else "unknown"

            ctx: Any = err.get("ctx")
            meta: Any | None = _sanitize_meta(value=ctx) if isinstance(ctx, dict) else None

            errors.append(
                ValidationErrorItem(
                    path=loc_str,
                    message=str(object=err.get("msg", "Invalid value")),
                    type=str(object=err.get("type", "validation_error")),
                    meta=meta,
                ),
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ValidationErrorResponse(
                error="Validation Error",
                errors=errors,
                timestamp=datetime.now(tz=UTC),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(exc_class_or_status_code=Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle Unhandled Application Exceptions.

        Arguments:
            request (Request): Incoming request.
            exc (Exception): Unhandled exception.

        Returns:
            JSONResponse: Standardized internal server error response.

        Raises:
            None
        """

        error_logger: logging.Logger = get_logger(name="server.general_exception")
        error_logger.error(
            msg=f"Unhandled exception: {type(exc).__name__} - {exc!s}",
            extra={
                "exception_type": type(exc).__name__,
                "exception_message": str(object=exc),
                "url": str(object=request.url),
                "method": request.method,
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An Unexpected Error Occurred",
                timestamp=datetime.now(tz=UTC),
            ).model_dump(mode="json"),
        )

    logger.info(msg="Adding API routes")
    api_router: APIRouter = create_api_router()
    app.include_router(router=api_router)

    logger.info(msg="FastAPI application initialized successfully")
    return app


app: FastAPI = create_app()


__all__: list[str] = ["app", "create_app"]
