# Third-Party Imports
import redis
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Local Imports
from config.settings import settings


# Rate Limit Middleware Class
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    IP-Based Rate Limiting Middleware

    This Middleware Implements IP-Based Rate Limiting Using Redis.
    It Limits the Number of Requests from a Single IP Address.
    """

    # Initialize Rate Limit Middleware
    def __init__(
        self,
        app: FastAPI,
        limit: int = 100,
        window: int = 60,
        exclude_routes: list[str] | None = None,
    ) -> None:
        """
        This Function Initializes the Rate Limit Middleware.

        Args:
            app (FastAPI): The FastAPI Application Instance
            limit (int): Maximum Number of Requests Allowed in Window. Defaults to 100
            window (int): Time Window in Seconds. Defaults to 60
            exclude_routes (list[str] | None): List of Route Paths to Exclude from Rate Limiting. Defaults to None
        """

        # Initialize Rate Limit Middleware
        super().__init__(app)

        # Initialize Rate Limit Configuration
        self.limit: int = limit
        self.window: int = window
        self.exclude_routes: list[str] = exclude_routes or []

        # Initialize Redis Client
        self.redis: redis.Redis = redis.Redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_HTTP_RATE_LIMIT_DB,
            decode_responses=True,
        )

    # Dispatch Method
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Dispatch Method for Rate Limit Middleware

        Args:
            request (Request): The Incoming Request
            call_next (RequestResponseEndpoint): The Next Middleware or Route Handler

        Returns:
            Response: The HTTP Response
        """

        # Check if Route is Excluded
        if request.url.path in self.exclude_routes:
            # Call Next Middleware or Route Handler
            return await call_next(request)

        # Get Client IP
        ip_address: str | None = request.client.host if request.client else None

        # If IP Address is Available
        if ip_address:
            # Create Redis Key
            key: str = f"rate_limit:{ip_address}"

            # Get Current Count
            current: int | None = self.redis.get(key)

            # If Count Exists
            if current:
                # Convert Current Count to Integer
                current: int = int(current)

                # If Limit Exceeded
                if current >= self.limit:
                    # Return Rate Limit Exceeded Response
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Rate Limit Exceeded"},
                    )

                # Increment Count
                self.redis.incr(name=key)

            else:
                # Set Initial Count with Expiration
                self.redis.setex(name=key, time=self.window, value=1)

        # Call Next Middleware or Route Handler
        return await call_next(request)


# Add Rate Limit Middleware Function
def add_rate_limit_middleware(app: FastAPI) -> None:
    """
    Add Rate Limit Middleware to FastAPI Application

    This Function Adds Rate Limit Middleware to the Provided FastAPI Application.

    Args:
        app (FastAPI): The FastAPI Application Instance
    """

    # Add Rate Limit Middleware
    app.add_middleware(
        middleware_class=RateLimitMiddleware,
        limit=settings.RATE_LIMIT,
        window=settings.RATE_LIMIT_WINDOW,
        exclude_routes=[
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/health",
        ],
    )


# Exports
__all__: list[str] = ["add_rate_limit_middleware"]
