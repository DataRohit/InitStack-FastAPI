# Third-Party Imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local Imports
from config.settings import settings


# Add CORS Middleware Function
def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS Middleware to FastAPI Application

    This Function Adds CORS Middleware to the Provided FastAPI Application
    with Configuration from Settings.

    Args:
        app (FastAPI): The FastAPI Application Instance.
    """

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


# Exports
__all__: list[str] = ["add_cors_middleware"]
