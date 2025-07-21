# Third-Party Imports
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Local Imports
from config.settings import settings


# Add HTTPS Redirect Middleware Function
def add_https_redirect_middleware(app: FastAPI) -> None:
    """
    Add HTTPS Redirect Middleware to FastAPI Application

    This middleware enforces HTTPS by redirecting HTTP requests to HTTPS.
    Only enabled when DEBUG is False in settings.

    Args:
        app (FastAPI): The FastAPI Application Instance.
    """

    # If DEBUG is False
    if not settings.DEBUG:
        # Add HTTPS Redirect Middleware
        app.add_middleware(HTTPSRedirectMiddleware)


# Exports
__all__: list[str] = ["add_https_redirect_middleware"]
