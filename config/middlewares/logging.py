# Standard Library Imports
import logging
import time
import uuid

# Third-Party Imports
import colorlog
from fastapi import FastAPI, Request
from starlette.types import Message, Receive, Scope, Send

# Configure Colored Logger
handler: colorlog.StreamHandler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(method)s %(path)s - %(message)s",
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
logger: logging.Logger = colorlog.getLogger(name=__name__)
logger.addHandler(hdlr=handler)
logger.setLevel(level=logging.INFO)
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

    # Check If Request Should Be Excluded
    def _should_exclude_request(self, request: Request) -> bool:
        """
        Check If Request Should Be Excluded

        Args:
            request (Request): FastAPI Request Instance

        Returns:
            bool: True if request should be excluded, False otherwise
        """

        # Check If Any Exclude Route Matches
        return any(request.url.path.startswith(route) for route in self.exclude_routes)

    # Log Request Information
    def _log_request_info(self, request: Request, request_id: str) -> None:
        """
        Log Request Information

        Args:
            request (Request): FastAPI Request Instance
            request_id (str): Unique Request ID
        """

        # Log Request
        logger.info(
            "[%s] %s %s - Client: %s - Agent: %s - Params: %s",
            request_id,
            request.method,
            request.url.path,
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
            dict(request.query_params),
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

    # Determine Log Level Based On Status Code
    def _get_log_level(self, status_code: int) -> int:
        """
        Determine Log Level Based On Status Code

        Args:
            status_code (int): HTTP Status Code

        Returns:
            int: Logging Level
        """

        # If Status Code Is 500 Or Higher
        if status_code >= 500:  # noqa: PLR2004
            # Return Error Level
            return logging.ERROR

        # If Status Code Is 400 Or Higher
        if status_code >= 400:  # noqa: PLR2004
            # Return Warning Level
            return logging.WARNING

        # Return Info Level
        return logging.INFO

    # Log Response Information
    def _log_response_info(
        self,
        request: Request,
        request_id: str,
        status_code: int,
        process_time: float,
        response_size: int,
    ) -> None:
        """
        Log Response Information

        Args:
            request (Request): FastAPI Request Instance
            request_id (str): Unique Request ID
            status_code (int): HTTP Status Code
            process_time (float): Request Process Time
            response_size (int): Response Size In Bytes
        """

        # Get Log Level
        log_level: int = self._get_log_level(status_code)

        # Log Response
        logger.log(
            log_level,
            "[%s] %s %s - %d (%.3fs) %d bytes - Client: %s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            process_time,
            response_size,
            request.client.host if request.client else None,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "process_time": process_time,
                "response_size": response_size,
                "client": request.client.host if request.client else None,
            },
        )

    # Create Send Function With Logging
    def _create_send_with_logging(self, request: Request, request_id: str, start_time: float, send: Send):
        """
        Create Send Function With Logging

        Args:
            request (Request): FastAPI Request Instance
            request_id (str): Unique Request ID
            start_time (float): Request Start Time
            send (Send): Original Send Function

        Returns:
            Callable: Send Function With Logging
        """

        # Define Send With Logging
        async def send_with_logging(message: Message) -> None:
            """
            Send Response With Logging

            Args:
                message (Message): FastAPI Message
            """

            # Handle HTTP Response Start
            if message["type"] == "http.response.start":
                # Get Response Details
                response_headers: dict = dict(message["headers"])
                response_size: int = int(response_headers.get(b"content-length", 0))
                status_code: int = int(message["status"])
                process_time: float = time.time() - start_time

                # Log Response Information
                self._log_response_info(request, request_id, status_code, process_time, response_size)

            # Send Message
            await send(message)

        # Return Send With Logging Function
        return send_with_logging

    # Log Exception Information
    def _log_exception_info(self, request: Request, request_id: str, exc: Exception) -> None:
        """
        Log Exception Information

        Args:
            request (Request): FastAPI Request Instance
            request_id (str): Unique Request ID
            exc (Exception): Exception Instance
        """

        # Initialize Error Message
        msg: str = f"Request Failed: {exc!s}"

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

    # Process Request And Log Details
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process Request And Log Details

        Args:
            scope (Scope): FastAPI Scope
            receive (Receive): Receive Callable
            send (Send): Send Callable
        """

        # Handle Non-HTTP Requests
        if scope["type"] != "http":
            # Call The Next Middleware
            await self.app(scope, receive, send)

            # Return
            return

        # Initialize Request
        request: Request = Request(scope, receive)

        # Handle Excluded Routes
        if self._should_exclude_request(request):
            # Call The Next Middleware
            await self.app(scope, receive, send)

            # Return
            return

        # Setup Request Logging
        request_id: str = str(uuid.uuid4())
        start_time: float = time.time()

        # Log Request Information
        self._log_request_info(request, request_id)

        # Create Send Function With Logging
        send_with_logging = self._create_send_with_logging(request, request_id, start_time, send)

        try:
            # Call The Next Middleware
            await self.app(scope, receive, send_with_logging)

        except Exception as exc:
            # Log Exception Information
            self._log_exception_info(request, request_id, exc)

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
            "/api/health",
        ],
    )


# Exports
__all__: list[str] = ["add_logging_middleware"]
