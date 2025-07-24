# Third-Party Imports
import pydantic_core
import sentry_sdk
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Local Imports
from config.connection_pool import lifespan
from config.middlewares import (
    add_compression_middleware,
    add_cors_middleware,
    add_https_redirect_middleware,
    add_logging_middleware,
    add_rate_limit_middleware,
    add_security_headers_middleware,
    add_trusted_host_middleware,
)
from config.settings import settings
from src.routes import health_router, users_router


# Create FastAPI Instance Function
def _create_fastapi_instance() -> FastAPI:
    """
    Create FastAPI Instance

    This Function Creates the FastAPI Application Instance
    with Required Metadata and Configuration.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """

    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        server_name=settings.PROJECT_NAME,
        sample_rate=settings.SENTRY_SAMPLE_RATE,
        send_default_pii=True,
    )

    # Initialize FastAPI with Metadata
    app: FastAPI = FastAPI(
        title=settings.PROJECT_NAME,
        summary=settings.PROJECT_SUMMARY,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        debug=settings.DEBUG,
        root_path=settings.API_PREFIX,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": settings.PROJECT_NAME,
            "url": settings.PROJECT_WEBSITE,
            "email": settings.PROJECT_EMAIL,
        },
        license_info={
            "name": "MIT License",
            "url": settings.LICENSE_URL,
        },
    )

    # Return Application Instance
    return app


# Setup 404 Handler Function
def _setup_404_handler(app: FastAPI) -> None:
    """
    Setup 404 Handler

    This Function Configures 404 Not Found Handler
    for the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # 404 Not Found Handler
    @app.exception_handler(status.HTTP_404_NOT_FOUND)
    async def not_found_exception_handler(request: Request, exc: HTTPException):
        """
        404 Not Found Handler

        Returns standardized JSON response for 404 errors.

        Returns:
            JSONResponse: Formatted error response
        """

        # Return Error Response
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Not Found"},
        )


# Setup 400 Handler Function
def _setup_400_handler(app: FastAPI) -> None:
    """
    Setup 400 Handler

    This Function Configures 400 Bad Request Handler
    for the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # 400 Bad Request Handler
    @app.exception_handler(pydantic_core.ValidationError)
    async def bad_request_exception_handler(request: Request, exc: pydantic_core.ValidationError):
        """
        400 Bad Request Handler

        Returns standardized JSON response for 400 errors.

        Returns:
            JSONResponse: Formatted error response
        """

        # Get Error Data
        error_data: dict = exc.errors()

        # Traverse Error Data
        for idx in range(len(error_data)):
            # Extract Error Field
            field = error_data[idx]["loc"][0]

            # If error in Error ctx
            if "error" in error_data[idx]["ctx"]:
                # Update Error Message
                error_data[idx] = {
                    "field": field,
                    "reason": error_data[idx]["ctx"]["error"].args[0]["reason"].strip(".").title(),
                }

            # If reason in Error ctx
            elif "reason" in error_data[idx]["ctx"]:
                # Update Error Message
                error_data[idx] = {
                    "field": field,
                    "reason": error_data[idx]["ctx"]["reason"].strip(".").title(),
                }

        # Return JSON Response
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Validation Error",
                "errors": error_data,
            },
        )


# Setup 422 Handler Function
def _setup_422_handler(app: FastAPI) -> None:
    """
    Setup 422 Handler

    This Function Configures 422 Validation Error Handler
    for the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # 422 Validation Error Handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        422 Validation Error Handler

        Returns Detailed Validation Error Information.

        Returns:
            JSONResponse: Formatted Error Response with Validation Details
        """

        # List to Store Errors
        errors = []

        # Traverse Error Data
        for error in exc.errors():
            # Update Error Message to Title Case
            error["msg"] = error["msg"].title()

            # If reason is in ctx
            if error.get("ctx") and "reason" in error["ctx"]:
                # Update Ctx Reason
                error["ctx"]["reason"] = error["ctx"]["reason"].title()

            # Append Error to List
            errors.append(error)

        # Return Error Response
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Invalid Request",
                "errors": errors,
            },
        )


# Setup 500 Handler Function
def _setup_500_handler(app: FastAPI) -> None:
    """
    Setup 500 Handler

    This Function Configures 500 Internal Server Error Handler
    for the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # 500 Internal Server Error Handler
    @app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
    async def internal_exception_handler(request: Request, exc: Exception):
        """
        500 Internal Server Error Handler

        Returns Standardized Response for Server Errors.

        Returns:
            JSONResponse: Formatted Error Response
        """

        # Return Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )


# Setup Global Handler Function
def _setup_global_handler(app: FastAPI) -> None:
    """
    Setup Global Handler

    This Function Configures Global Exception Handler
    for the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # Exception Handler
    @app.exception_handler(exc_class_or_status_code=Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        Global Exception Handler

        This Function Handles All Unhandled Exceptions.

        Args:
            request (Request): The Request That Caused the Exception.
            exc (Exception): The Exception That Was Raised.

        Returns:
            JSONResponse: Error response with status code and message.
        """

        # Return Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )


# Setup Exception Handlers Function
def _setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup Exception Handlers

    This Function Configures All Exception Handlers
    for the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # Setup 404 Handler
    _setup_404_handler(app)

    # Setup 400 Handler
    _setup_400_handler(app)

    # Setup 422 Handler
    _setup_422_handler(app)

    # Setup 500 Handler
    _setup_500_handler(app)

    # Setup Global Handler
    _setup_global_handler(app)


# Setup Middleware Function
def _setup_middleware(app: FastAPI) -> None:
    """
    Setup Middleware

    This Function Adds All Required Middleware
    to the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # Add HTTPS Redirect Middleware
    add_https_redirect_middleware(app)

    # Add Trusted Host Middleware
    add_trusted_host_middleware(app)

    # Add Security Headers Middleware
    add_security_headers_middleware(app)

    # Add CORS Middleware
    add_cors_middleware(app)

    # Add Rate Limit Middleware
    add_rate_limit_middleware(app)

    # Add Compression Middleware
    add_compression_middleware(app)

    # Add Logging Middleware
    add_logging_middleware(app)


# Setup Routers Function
def _setup_routers(app: FastAPI) -> None:
    """
    Setup Routers

    This Function Mounts All Required Routers
    to the FastAPI Application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    # Mount Routers
    app.include_router(health_router)
    app.include_router(users_router)


# Initialize FastAPI Application
def create_app() -> FastAPI:
    """
    Create App Function

    This Function Initializes the FastAPI Application
    with Required Metadata, Middleware and Lifespan.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """

    # Create FastAPI Instance
    app: FastAPI = _create_fastapi_instance()

    # Setup Exception Handlers
    _setup_exception_handlers(app)

    # Setup Middleware
    _setup_middleware(app)

    # Setup Routers
    _setup_routers(app)

    # Return Application Instance
    return app


# Create the Application Instance
app: FastAPI = create_app()

# Exports
__all__: list[str] = ["app"]
