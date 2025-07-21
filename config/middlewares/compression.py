# Third-Party Imports
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

# Local Imports
from config.settings import settings


# Add Compression Middleware Function
def add_compression_middleware(app: FastAPI) -> None:
    """
    Add Compression Middleware To FastAPI Application

    This Function Adds GZip Compression Middleware To The Provided FastAPI Application.
    It Configures Compression Based On Application Settings.

    Args:
        app (FastAPI): FastAPI Application Instance
    """

    # Add GZip Middleware With Configuration
    app.add_middleware(
        middleware_class=GZipMiddleware,
        minimum_size=settings.COMPRESSION_MIN_SIZE,
        compresslevel=settings.COMPRESSION_LEVEL,
    )


# Exports
__all__: list[str] = ["add_compression_middleware"]
