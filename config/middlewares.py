import hashlib
import json
import time
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware

from config.adapters import RedisAdapter
from config.adapters import get_redis_adapter
from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from starlette.requests import Request


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware To Limit Request Body Size And Upload Size.

    Inherits:
        BaseHTTPMiddleware

    Attributes:
        max_request_size (int): Maximum request body size in bytes.
        max_upload_size (int): Maximum upload file size in bytes.

    Properties:
        None

    Methods:
        dispatch: Process request and check size limits.
    """

    def __init__(self, app, max_request_size: int = 16777216, max_upload_size: int = 104857600):
        """Initialize Request Size Limit Middleware.

        Arguments:
            app: ASGI application.
            max_request_size (int): Maximum request body size in bytes (default: 16MB).
            max_upload_size (int): Maximum upload file size in bytes (default: 100MB).

        Returns:
            None

        Raises:
            None
        """

        super().__init__(app)
        self.max_request_size: int = max_request_size
        self.max_upload_size: int = max_upload_size

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process Request And Check Size Limits.

        Arguments:
            request (Request): Incoming request.
            call_next: Next middleware or endpoint.

        Returns:
            Response: HTTP response.

        Raises:
            HTTPException: If request size exceeds limits.
        """

        content_length: str | None = request.headers.get("content-length")
        if content_length:
            content_length: int = int(content_length)
            content_type: str = request.headers.get("content-type", default="")  # ty:ignore[no-matching-overload]

            if "multipart/form-data" in content_type:
                if content_length > self.max_upload_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload size {content_length} bytes exceeds maximum allowed {self.max_upload_size} bytes",  # noqa: E501
                    )
            elif content_length > self.max_request_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request size {content_length} bytes exceeds maximum allowed {self.max_request_size} bytes",
                )

        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware For Request And Response Logging.

    Inherits:
        BaseHTTPMiddleware

    Attributes:
        logger (logging.Logger): Logger instance for request/response logging.

    Properties:
        None

    Methods:
        dispatch: Process request and log request/response information.
    """

    def __init__(self, app):
        """Initialize Logging Middleware.

        Arguments:
            app: ASGI application.

        Returns:
            None

        Raises:
            None
        """

        super().__init__(app)
        self.logger: logging.Logger = get_logger(name="middleware.logging")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process Request And Log Request/Response Information.

        Arguments:
            request (Request): Incoming request.
            call_next: Next middleware or endpoint.

        Returns:
            Response: HTTP response.

        Raises:
            None
        """

        if request.url.path in ("/docs", "/redoc", "/openapi.json", "/api/v1/health"):
            return await call_next(request)

        start_time: int | float = time.time()

        client_ip: str = request.client.host if request.client else "unknown"
        method: str = request.method
        path: str = request.url.path
        user_agent: str = request.headers.get("user-agent", default="unknown")  # ty:ignore[no-matching-overload]

        self.logger.info(
            msg=f"Request started: {method} {path}",
            extra={
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "user_agent": user_agent,
                "request_id": id(request),
            },
        )

        try:
            response: Response = await call_next(request)
            process_time: int | float = time.time() - start_time

            self.logger.info(
                msg=f"Request completed: {method} {path} - {response.status_code}",
                extra={
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "process_time": round(number=process_time, ndigits=4),
                    "request_id": id(request),
                },
            )

            response.headers["X-Process-Time"] = str(object=process_time)

        except Exception as exc:
            process_time: int | float = time.time() - start_time

            self.logger.exception(
                msg=f"Request failed: {method} {path} - {type(exc).__name__}",
                extra={
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "exception": str(object=exc),
                    "process_time": round(number=process_time, ndigits=4),
                    "request_id": id(request),
                },
            )
            raise

        else:
            return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Production-Grade Rate Limiting Middleware With Atomic Redis Operations.

    This middleware implements bulletproof rate limiting using atomic Redis INCR operations
    to prevent race conditions and ensure accurate rate limiting under high concurrency.

    Inherits:
        BaseHTTPMiddleware

    Attributes:
        logger (logging.Logger): Logger instance for rate limiting operations.
        redis_adapter (RedisAdapter | None): Redis adapter for rate limit storage.
        requests_per_minute (int): Maximum requests per minute per client.
        window_size (int): Rate limit window size in seconds.
        redis_key_prefix (str): Redis key prefix for rate limiting.
        redis_key_expiry (int): Redis key expiry in seconds.
        exempt_ips (set[str]): IP addresses exempt from rate limiting.
        header_enabled (bool): Include rate limit headers in responses.
        retry_after_header (bool): Include Retry-After header when rate limited.

    Properties:
        None

    Methods:
        dispatch: Process request and apply rate limiting.
        _get_client_ip: Get client IP address from request.
        _get_client_identifier: Get unique client identifier.
        _get_rate_limit_key: Generate Redis key for rate limiting.
        _apply_rate_limit: Apply rate limiting using atomic Redis operations.
        _add_rate_limit_headers: Add rate limit headers to response.
        _is_exempt_ip: Check if IP is exempt from rate limiting.
    """

    def __init__(self, app):
        """Initialize Rate Limit Middleware.

        Arguments:
            app: ASGI application.

        Returns:
            None

        Raises:
            None
        """

        super().__init__(app)
        self.logger: logging.Logger = get_logger(name="middleware.rate_limit")
        self.redis_adapter: RedisAdapter | None = None
        self.requests_per_minute: int = settings.rate_limit_requests_per_minute
        self.window_size: int = settings.rate_limit_window_size
        self.redis_key_prefix: str = settings.rate_limit_redis_key_prefix
        self.redis_key_expiry: int = settings.rate_limit_redis_key_expiry
        self.exempt_ips: set[str] = set(settings.rate_limit_exempt_ips)
        self.header_enabled: bool = settings.rate_limit_header_enabled
        self.retry_after_header: bool = settings.rate_limit_retry_after_header

        self.logger.info(
            msg="Rate limit middleware initialized",
            extra={
                "requests_per_minute": self.requests_per_minute,
                "window_size": self.window_size,
                "exempt_ips_count": len(self.exempt_ips),
            },
        )

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: C901
        """Process Request And Apply Rate Limiting Using Atomic Operations.

        Arguments:
            request (Request): Incoming request.
            call_next: Next middleware or endpoint.

        Returns:
            Response: HTTP response.

        Raises:
            HTTPException: If rate limit exceeded (HTTP 429).
        """

        if not settings.rate_limit_enabled:
            return await call_next(request)

        client_ip: str = self._get_client_ip(request)

        if self._is_exempt_ip(client_ip):
            self.logger.debug(
                msg="Request from exempt IP, skipping rate limiting",
                extra={"client_ip": client_ip},
            )
            return await call_next(request)

        if not settings.redis_enabled:
            self.logger.warning(
                msg="Rate limiting requires Redis but Redis is disabled, allowing request",
                extra={"client_ip": client_ip},
            )
            return await call_next(request)

        try:
            if self.redis_adapter is None:
                self.redis_adapter: RedisAdapter = await get_redis_adapter()

            client_id: str = self._get_client_identifier(request)
            rate_limit_key: str = self._get_rate_limit_key(client_id)

            is_allowed: bool
            current_count: int
            reset_time: int | float
            is_allowed, current_count, reset_time = await self._apply_rate_limit(rate_limit_key)

            if not is_allowed:
                retry_after: int = max(1, int(reset_time - time.time()))

                self.logger.warning(
                    msg="Rate limit exceeded",
                    extra={
                        "client_ip": client_ip,
                        "client_id": client_id,
                        "current_count": current_count,
                        "limit": self.requests_per_minute,
                        "retry_after": retry_after,
                        "rate_limit_key": rate_limit_key,
                    },
                )

                response_body: dict[str, str] = {
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "timestamp": datetime.now(tz=UTC).isoformat(),
                }

                headers: dict[str, str] = {
                    "content-type": "application/json",
                }

                if self.header_enabled:
                    headers.update(
                        {
                            "X-RateLimit-Limit": str(object=self.requests_per_minute),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(object=int(reset_time)),
                        },
                    )

                if self.retry_after_header:
                    headers["Retry-After"] = str(object=retry_after)

                return Response(
                    content=json.dumps(obj=response_body),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers=headers,
                )

            response: Response = await call_next(request)

            if self.header_enabled:
                remaining: int = max(0, self.requests_per_minute - current_count)
                self._add_rate_limit_headers(response, remaining, reset_time)

            self.logger.debug(
                msg="Request processed within rate limit",
                extra={
                    "client_ip": client_ip,
                    "client_id": client_id,
                    "current_count": current_count,
                    "limit": self.requests_per_minute,
                    "remaining": max(0, self.requests_per_minute - current_count),
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self.logger.exception(
                msg=f"Rate limiting error, allowing request: {exc!s}",
                extra={
                    "client_ip": client_ip,
                    "exception_type": type(exc).__name__,
                },
            )
            return await call_next(request)

        else:
            return response

    def _get_client_ip(self, request: Request) -> str:
        """Get Client IP Address From Request Headers.

        Arguments:
            request (Request): Incoming request.

        Returns:
            str: Client IP address.

        Raises:
            None
        """

        forwarded_for: str | None = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(sep=",")[0].strip()

        real_ip: str | None = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        return request.client.host if request.client else "unknown"

    def _get_client_identifier(self, request: Request) -> str:
        """Get Unique Client Identifier Using IP And User-Agent.

        Arguments:
            request (Request): Incoming request.

        Returns:
            str: Unique client identifier hash (16 characters).

        Raises:
            None
        """

        client_ip: str = self._get_client_ip(request)
        user_agent: str = request.headers.get("user-agent", default="")  # ty:ignore[no-matching-overload]

        identifier_string = f"{client_ip}:{user_agent}"
        client_hash: str = hashlib.sha256(data=identifier_string.encode()).hexdigest()[:16]

        return client_hash

    def _get_rate_limit_key(self, client_id: str) -> str:
        """Generate Redis Key For Rate Limiting Based On Time Window.

        Arguments:
            client_id (str): Client identifier.

        Returns:
            str: Redis key for rate limiting.

        Raises:
            None
        """

        current_window: int = int(time.time()) // self.window_size
        return f"{self.redis_key_prefix}:{client_id}:{current_window}"

    async def _apply_rate_limit(self, rate_limit_key: str) -> tuple[bool, int, float]:
        """Apply Rate Limiting Using Atomic Redis INCR Operation.

        This method uses Redis INCR which is atomic and thread-safe, preventing
        race conditions that can occur with separate GET/SET operations.

        Arguments:
            rate_limit_key (str): Redis key for rate limiting.

        Returns:
            tuple[bool, int, float]: (is_allowed, current_count, reset_time).

        Raises:
            Exception: If Redis operation fails.
        """

        try:
            current_count: int = await self.redis_adapter.incr(key=rate_limit_key)  # ty:ignore[possibly-missing-attribute]

            if current_count == 1:
                await self.redis_adapter.expire(key=rate_limit_key, time=self.redis_key_expiry)  # ty:ignore[possibly-missing-attribute]

            current_window: int = int(time.time()) // self.window_size
            reset_time: float = (current_window + 1) * self.window_size

            is_allowed: bool = current_count <= self.requests_per_minute

            self.logger.debug(
                msg="Rate limit applied",
                extra={
                    "rate_limit_key": rate_limit_key,
                    "current_count": current_count,
                    "limit": self.requests_per_minute,
                    "is_allowed": is_allowed,
                    "reset_time": reset_time,
                },
            )

        except Exception as exc:
            self.logger.exception(
                msg=f"Failed to apply rate limit: {exc!s}",
                extra={
                    "rate_limit_key": rate_limit_key,
                    "exception_type": type(exc).__name__,
                },
            )
            return True, 0, time.time() + self.window_size

        else:
            return is_allowed, current_count, reset_time

    def _add_rate_limit_headers(self, response: Response, remaining: int, reset_time: float) -> None:
        """Add Rate Limit Headers To Response.

        Arguments:
            response (Response): HTTP response.
            remaining (int): Remaining requests in current window.
            reset_time (float): Window reset time as timestamp.

        Returns:
            None

        Raises:
            None
        """

        response.headers["X-RateLimit-Limit"] = str(object=self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(object=remaining)
        response.headers["X-RateLimit-Reset"] = str(object=int(reset_time))

    def _is_exempt_ip(self, client_ip: str) -> bool:
        """Check If IP Is Exempt From Rate Limiting.

        Arguments:
            client_ip (str): Client IP address.

        Returns:
            bool: True if IP is exempt, False otherwise.

        Raises:
            None
        """

        return client_ip in self.exempt_ips


__all__: list[str] = ["LoggingMiddleware", "RateLimitMiddleware", "RequestSizeLimitMiddleware"]
