from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from config.logger import LoggerManager
from config.logger import get_logger
from config.middlewares import LoggingMiddleware
from config.middlewares import RequestSizeLimitMiddleware
from config.routes import create_api_router
from config.settings import settings
from src.models.base import ErrorResponse

if TYPE_CHECKING:
    import logging

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


def create_app() -> FastAPI:
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
    )

    logger.info(msg="Adding logging middleware")
    app.add_middleware(middleware_class=LoggingMiddleware)  # ty:ignore[invalid-argument-type]

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

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Validation Error",
                detail=str(object=exc),
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
    api_router = create_api_router()
    app.include_router(router=api_router)

    logger.info(msg="FastAPI application initialized successfully")
    return app


app: FastAPI = create_app()


__all__: list[str] = ["app", "create_app"]
