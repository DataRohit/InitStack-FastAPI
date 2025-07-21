# Standard Library Imports
import logging
import time
import uuid

# Third-Party Imports
import colorlog
from fastapi import FastAPI, Request
from starlette.types import Message, Receive, Scope, Send

# Configure Colored Logger
handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    ),
)
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


# Logging Middleware Class
class LoggingMiddleware:
    """
    Logging Middleware Class

    This Middleware Adds Structured Request/Response Logging
    To The FastAPI Application.
    """

    # Initialize Logging Middleware
    def __init__(self, app: FastAPI, exclude_routes: list[str] | None = None) -> None:
        """
        Initialize Logging Middleware

        Args:
            app (FastAPI): FastAPI Application Instance
            exclude_routes (list[str] | None): List of routes to exclude from logging
        """

        # Initialize Logging Middleware
        self.app: FastAPI = app
        self.exclude_routes: list[str] = exclude_routes or []

    # Process Request And Log Details
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process Request And Log Details

        Args:
            scope (Scope): FastAPI Scope
            receive (Receive): Receive Callable
            send (Send): Send Callable
        """

        # If The Scope Is Not HTTP
        if scope["type"] != "http":
            # Call The Next Middleware
            await self.app(scope, receive, send)

            # Return
            return

        # Initialize Request
        request = Request(scope, receive)

        # Skip logging for excluded routes
        if any(request.url.path.startswith(route) for route in self.exclude_routes):
            # Call The Next Middleware
            await self.app(scope, receive, send)

            # Return
            return

        # Generate Request ID
        request_id = str(uuid.uuid4())

        # Get Start Time
        start_time = time.time()

        # Initialize Request
        request = Request(scope, receive)

        # Log Request
        logger.info(
            "Request: %s %s",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Process Request
        async def send_with_logging(message: Message) -> None:
            """
            Send Response With Logging

            Args:
                message (Message): FastAPI Message
            """

            # If The Message Type Is HTTP Response Start
            if message["type"] == "http.response.start":
                # Initialize Response Headers
                response_headers = dict(message["headers"])

                # Initialize Response Size
                response_size = int(response_headers.get(b"content-length", 0))

                # Calculate Process Time
                process_time = time.time() - start_time

                # Log Response
                logger.info(
                    "Response: %s %s - %s (%.3fs) %s bytes",
                    request.method,
                    request.url.path,
                    message["status"],
                    process_time,
                    response_size,
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": message["status"],
                        "process_time": process_time,
                        "response_size": response_size,
                    },
                )

            # Send Message
            await send(message)

        try:
            # Call The Next Middleware
            await self.app(scope, receive, send_with_logging)

        except Exception as exc:
            # Initialize Error Message
            msg = f"Request Failed: {exc!s}"

            # Log The Error
            logger.exception(
                msg=msg,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                },
            )

            # Raise The Exception
            raise


# Add Logging Middleware Function
def add_logging_middleware(app: FastAPI) -> None:
    """
    Add Logging Middleware To FastAPI Application

    Args:
        app (FastAPI): FastAPI Application Instance
    """

    # Add Logging Middleware
    app.add_middleware(
        middleware_class=LoggingMiddleware,
        exclude_routes=[
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/health/",
        ],
    )


# Exports
__all__: list[str] = ["add_logging_middleware"]
