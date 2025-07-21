# Third-Party Imports
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Local Imports
from config.settings import settings


# Add Trusted Host Middleware Function
def add_trusted_host_middleware(app: FastAPI) -> None:
    """
    Add Trusted Host Middleware to FastAPI Application

    This Function Adds Trusted Host Middleware to the Provided FastAPI Application
    with Configuration from Settings.

    Args:
        app (FastAPI): The FastAPI Application Instance.
    """

    # If DEBUG is False
    if not settings.DEBUG:
        # Add Trusted Host Middleware
        app.add_middleware(
            middleware_class=TrustedHostMiddleware,
            allowed_hosts=[host.strip() for host in settings.ALLOWED_HOSTS.split(",")],
        )


# Exports
__all__: list[str] = ["add_trusted_host_middleware"]
