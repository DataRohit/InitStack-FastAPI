# Third-Party Imports
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Local Imports
from config.settings import settings
from src.routes import health_router


# Initialize FastAPI Application
def create_app() -> FastAPI:
    """
    Create App Function

    This Function Initializes the FastAPI Application
    with Required Metadata and Middleware.

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

    # If CORS Origins are Configured
    if settings.CORS_ORIGINS:
        # Add CORS Middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin).strip() for origin in settings.CORS_ORIGINS.split(",")],
            allow_credentials=settings.CORS_CREDENTIALS,
            allow_methods=[str(method).strip() for method in settings.CORS_METHODS.split(",")],
            allow_headers=[str(header).strip() for header in settings.CORS_HEADERS.split(",")],
            max_age=settings.CORS_MAX_AGE,
        )

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
