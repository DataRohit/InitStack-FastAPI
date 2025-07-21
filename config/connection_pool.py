# Standard Library Imports
import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# Third-Party Imports
import httpx
from fastapi import FastAPI

from config.mongodb import mongodb_manager

# Local Imports
from config.settings import settings


# Lifespan Function
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application Lifespan Manager Function

    This Function Manages the Application Lifespan by:
    - Creating Connection Pools
    - Initializing MongoDB Adapter
    - Proper Timeout Configuration
    - Connection Limits
    - TLS Verification
    - Connection Reuse

    Args:
        app (FastAPI): FastAPI application instance
    """

    # Initialize MongoDB Connection
    await mongodb_manager.client.admin.command("ping")

    # Create SSL Context
    ssl_context: ssl.SSLContext = ssl.create_default_context()

    # If SSL Verification is Disabled
    if not settings.SSL_VERIFY:
        # Disable SSL Verification
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    # Configure Connection Limits
    limits: httpx.Limits = httpx.Limits(
        max_connections=settings.HTTP_MAX_CONNECTIONS,
        max_keepalive_connections=settings.HTTP_KEEPALIVE_CONNECTIONS,
        keepalive_expiry=settings.HTTP_KEEPALIVE_EXPIRY,
    )

    # Configure Timeout
    timeout: httpx.Timeout = httpx.Timeout(
        timeout=settings.HTTP_TIMEOUT,
        connect=settings.HTTP_TIMEOUT_CONNECT,
        read=settings.HTTP_TIMEOUT_READ,
        write=settings.HTTP_TIMEOUT_WRITE,
        pool=settings.HTTP_TIMEOUT_POOL,
    )

    # Configure HTTP Client
    app.state.http_client: httpx.AsyncClient = httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        verify=ssl_context,
        http2=settings.HTTP2_ENABLED,
    )

    try:
        # Yield Application
        yield

    finally:
        # Close HTTP Client
        await app.state.http_client.aclose()


# Get HTTP Client
def get_http_client(app: FastAPI) -> httpx.AsyncClient:
    """
    Get HTTP Client from Application State

    Args:
        app (FastAPI): FastAPI application instance

    Returns:
        httpx.AsyncClient: Configured async HTTP client
    """

    # Return HTTP Client
    return app.state.http_client


# Exports
__all__: list[str] = ["get_http_client", "lifespan"]
