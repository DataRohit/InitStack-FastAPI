import logging
import sys
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

from config.middlewares import RequestSizeLimitMiddleware
from config.settings import settings
from src.models.base import ErrorResponse

if TYPE_CHECKING:
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

    log_level: str = getattr(logging, settings.log_level.upper())

    if settings.log_format == "json":
        logging.basicConfig(
            level=log_level,
            format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
            handlers=[logging.StreamHandler(stream=sys.stdout)],
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(stream=sys.stdout)],
        )


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

    app.add_middleware(
        middleware_class=CORSMiddleware,  # ty:ignore[invalid-argument-type]
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    if settings.proxy_headers_enabled:
        app.add_middleware(
            middleware_class=ProxyHeadersMiddleware,  # ty:ignore[invalid-argument-type]
            trusted_hosts=settings.proxy_headers_trusted_hosts,
        )

    app.add_middleware(
        middleware_class=RequestSizeLimitMiddleware,  # ty:ignore[invalid-argument-type]
        max_request_size=settings.max_request_size,
        max_upload_size=settings.max_upload_size,
    )

    if not settings.debug:
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

        logging.exception(msg="Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An Unexpected Error Occurred",
                timestamp=datetime.now(tz=UTC),
            ).model_dump(mode="json"),
        )

    return app


app: FastAPI = create_app()


__all__: list[str] = ["app", "create_app"]
