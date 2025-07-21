# Third-Party Imports
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
from src.routes import health_router


# Initialize FastAPI Application
def create_app() -> FastAPI:
    """
    Create App Function

    This Function Initializes the FastAPI Application
    with Required Metadata, Middleware and Lifespan.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """

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

    # 404 Not Found Handler
    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: HTTPException):
        """
        404 Not Found Handler

        Returns standardized JSON response for 404 errors.

        Returns:
            JSONResponse: Formatted error response
        """

        # Return Error Response
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found!"},
        )

    # 422 Validation Error Handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        422 Validation Error Handler

        Returns detailed validation error information.

        Returns:
            JSONResponse: Formatted error response with validation details
        """

        # Return Error Response
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation Error!",
                "errors": exc.errors(),
                "body": exc.body,
            },
        )

    # 500 Internal Server Error Handler
    @app.exception_handler(500)
    async def internal_exception_handler(request: Request, exc: Exception):
        """
        500 Internal Server Error Handler

        Returns standardized response for server errors.

        Returns:
            JSONResponse: Formatted error response
        """

        # Return Error Response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error!"},
        )

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

    # Mount Health Router
    app.include_router(health_router)

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
            content={"detail": "Internal Server Error!"},
        )

    # Return Application Instance
    return app


# Create the Application Instance
app: FastAPI = create_app()

# Exports
__all__: list[str] = ["app"]
