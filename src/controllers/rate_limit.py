import asyncio
import hashlib
import time
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status

from config.adapters.redis import get_redis_adapter
from config.logger import get_logger
from config.settings import settings
from src.schemas.base import ErrorResponse
from src.schemas.rate_limit import RateLimitConfig
from src.schemas.rate_limit import RateLimitStatus
from src.schemas.rate_limit import RateLimitStatusResponse
from src.schemas.rate_limit import RateLimitTestResponse
from src.schemas.rate_limit import RateLimitTestResult

if TYPE_CHECKING:
    import logging
    from collections.abc import Coroutine

    from config.adapters.redis import RedisAdapter


class RateLimitController:
    """Rate Limiting Management Controller For Testing And Monitoring.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for rate limiting operations.
        router (APIRouter): FastAPI router for rate limiting endpoints.

    Properties:
        None

    Methods:
        get_rate_limit_status: Get current rate limiting status and configuration.
        test_rate_limiting: Test rate limiting functionality with multiple requests.
        _setup_routes: Setup FastAPI routes for rate limiting endpoints.
        _check_rate_limit_enabled: Check if rate limiting is enabled.
        _get_client_identifier: Get unique client identifier.
        _get_rate_limit_key: Generate Redis key for rate limiting.
        _get_current_rate_limit_status: Get current rate limit status for client.
        _perform_rate_limit_test: Perform rate limiting test with multiple requests.
        _get_client_ip: Get client IP address from request.
    """

    def __init__(self) -> None:
        """Initialize Rate Limit Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.rate_limit")
        self.router: APIRouter = APIRouter(prefix="/rate-limit", tags=["Rate Limiting"])
        self._setup_routes()

        self._logger.info(msg="Rate limit controller initialized")

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For Rate Limiting Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.get(
            path="/status",
            response_model=RateLimitStatusResponse,
            status_code=status.HTTP_200_OK,
            summary="Get Rate Limiting Status",
            description="Get comprehensive rate limiting configuration and current status for the requesting client.",
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during rate limiting status check",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rate_limit_status_error": {
                                    "summary": "Rate limiting status check error",
                                    "description": "Example response when rate limiting status check encounters an internal error",  # noqa: E501
                                    "value": {
                                        "error": "Internal Server Error",
                                        "detail": "An Unexpected Error Occurred",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_429_TOO_MANY_REQUESTS: {
                    "description": "Rate limit exceeded",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rate_limit_exceeded": {
                                    "summary": "Rate limit exceeded",
                                    "description": "Example response when client exceeds rate limit",
                                    "value": {
                                        "error": "Too Many Requests",
                                        "detail": "Rate limit exceeded. Try again in 30 seconds.",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                    "headers": {
                        "X-RateLimit-Limit": {
                            "description": "Request limit per window",
                            "schema": {"type": "string", "example": "60"},
                        },
                        "X-RateLimit-Remaining": {
                            "description": "Remaining requests in current window",
                            "schema": {"type": "string", "example": "0"},
                        },
                        "X-RateLimit-Reset": {
                            "description": "Window reset time as Unix timestamp",
                            "schema": {"type": "string", "example": "1704110100"},
                        },
                        "Retry-After": {
                            "description": "Seconds to wait before retrying",
                            "schema": {"type": "string", "example": "30"},
                        },
                    },
                },
                status.HTTP_200_OK: {
                    "description": "Rate limiting status retrieved successfully",
                    "model": RateLimitStatusResponse,
                    "headers": {
                        "X-RateLimit-Limit": {
                            "description": "Request limit per window (when rate limiting enabled)",
                            "schema": {"type": "string", "example": "60"},
                        },
                        "X-RateLimit-Remaining": {
                            "description": "Remaining requests in current window (when rate limiting enabled)",
                            "schema": {"type": "string", "example": "59"},
                        },
                        "X-RateLimit-Reset": {
                            "description": "Window reset time as Unix timestamp (when rate limiting enabled)",
                            "schema": {"type": "string", "example": "1704110100"},
                        },
                    },
                    "content": {
                        "application/json": {
                            "examples": {
                                "rate_limiting_active": {
                                    "summary": "Rate limiting active",
                                    "description": "Example response when rate limiting is enabled and Redis is available",  # noqa: E501
                                    "value": {
                                        "rate_limiting_enabled": True,
                                        "redis_available": True,
                                        "config": {
                                            "enabled": True,
                                            "requests_per_minute": 60,
                                            "burst_size": 10,
                                            "window_size": 60,
                                            "redis_key_prefix": "rate_limit",
                                            "redis_key_expiry": 3600,
                                            "exempt_ips": ["127.0.0.1", "::1"],
                                            "header_enabled": True,
                                            "retry_after_header": True,
                                        },
                                        "current_status": {
                                            "client_id": "a1b2c3d4e5f6g7h8",
                                            "client_ip": "192.168.1.100",
                                            "current_count": 5,
                                            "limit": 60,
                                            "remaining": 55,
                                            "reset_time": "2025-01-01T12:35:00Z",
                                            "is_exempt": False,
                                            "window_start": "2025-01-01T12:34:00Z",
                                        },
                                        "timestamp": "2025-01-01T12:34:30Z",
                                    },
                                },
                                "rate_limiting_disabled": {
                                    "summary": "Rate limiting disabled",
                                    "description": "Example response when rate limiting is disabled",
                                    "value": {
                                        "rate_limiting_enabled": False,
                                        "redis_available": True,
                                        "config": {
                                            "enabled": False,
                                            "requests_per_minute": 60,
                                            "burst_size": 10,
                                            "window_size": 60,
                                            "redis_key_prefix": "rate_limit",
                                            "redis_key_expiry": 3600,
                                            "exempt_ips": ["127.0.0.1", "::1"],
                                            "header_enabled": True,
                                            "retry_after_header": True,
                                        },
                                        "current_status": None,
                                        "timestamp": "2025-01-01T12:34:30Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_rate_limit_status_endpoint(request: Request) -> RateLimitStatusResponse:
            """Get Rate Limiting Status Endpoint.

            Arguments:
                request (Request): Incoming request for client identification.

            Returns:
                RateLimitStatusResponse: Rate limiting status and configuration.

            Raises:
                HTTPException: If status check fails.
            """

            return await self.get_rate_limit_status(request)

        @self.router.post(
            path="/test",
            response_model=RateLimitTestResponse,
            status_code=status.HTTP_200_OK,
            summary="Test Rate Limiting",
            description="Perform comprehensive rate limiting testing by sending multiple requests to verify rate limiting behavior.",  # noqa: E501
            responses={
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during rate limiting test",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rate_limit_test_error": {
                                    "summary": "Rate limiting test error",
                                    "description": "Example response when rate limiting test encounters an internal error",  # noqa: E501
                                    "value": {
                                        "error": "Internal Server Error",
                                        "detail": "An Unexpected Error Occurred",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_429_TOO_MANY_REQUESTS: {
                    "description": "Rate limit exceeded",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rate_limit_exceeded": {
                                    "summary": "Rate limit exceeded",
                                    "description": "Example response when client exceeds rate limit",
                                    "value": {
                                        "error": "Too Many Requests",
                                        "detail": "Rate limit exceeded. Try again in 30 seconds.",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                    "headers": {
                        "X-RateLimit-Limit": {
                            "description": "Request limit per window",
                            "schema": {"type": "string", "example": "60"},
                        },
                        "X-RateLimit-Remaining": {
                            "description": "Remaining requests in current window",
                            "schema": {"type": "string", "example": "0"},
                        },
                        "X-RateLimit-Reset": {
                            "description": "Window reset time as Unix timestamp",
                            "schema": {"type": "string", "example": "1704110100"},
                        },
                        "Retry-After": {
                            "description": "Seconds to wait before retrying",
                            "schema": {"type": "string", "example": "30"},
                        },
                    },
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY: {
                    "description": "Validation error in request parameters",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "validation_error": {
                                    "summary": "Parameter validation error",
                                    "description": "Example response when request parameters fail validation",
                                    "value": {
                                        "error": "Validation Error",
                                        "detail": "Input validation failed",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_400_BAD_REQUEST: {
                    "description": "Bad request - invalid parameters",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "invalid_num_requests": {
                                    "summary": "Invalid number of requests",
                                    "description": "Example response when num_requests parameter is invalid",
                                    "value": {
                                        "error": "Bad Request",
                                        "detail": "Number of requests must be between 1 and 200",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_200_OK: {
                    "description": "Rate limiting test completed successfully",
                    "model": RateLimitTestResponse,
                    "headers": {
                        "X-RateLimit-Limit": {
                            "description": "Request limit per window (when rate limiting enabled)",
                            "schema": {"type": "string", "example": "60"},
                        },
                        "X-RateLimit-Remaining": {
                            "description": "Remaining requests in current window (when rate limiting enabled)",
                            "schema": {"type": "string", "example": "59"},
                        },
                        "X-RateLimit-Reset": {
                            "description": "Window reset time as Unix timestamp (when rate limiting enabled)",
                            "schema": {"type": "string", "example": "1704110100"},
                        },
                    },
                    "content": {
                        "application/json": {
                            "examples": {
                                "rate_limiting_working": {
                                    "summary": "Rate limiting working",
                                    "description": "Example response when rate limiting is working correctly",
                                    "value": {
                                        "rate_limiting_enabled": True,
                                        "redis_available": True,
                                        "test_requests_sent": 25,
                                        "requests_allowed": 20,
                                        "requests_blocked": 5,
                                        "first_block_at_request": 21,
                                        "total_test_duration_ms": 1234.56,
                                        "results": [
                                            {
                                                "request_number": 1,
                                                "allowed": True,
                                                "status_code": 200,
                                                "headers": {
                                                    "X-RateLimit-Limit": "20",
                                                    "X-RateLimit-Remaining": "19",
                                                    "X-RateLimit-Reset": "1704110100",
                                                },
                                                "duration_ms": 12.34,
                                                "error": None,
                                            },
                                            {
                                                "request_number": 61,
                                                "allowed": False,
                                                "status_code": 429,
                                                "headers": {
                                                    "X-RateLimit-Limit": "20",
                                                    "X-RateLimit-Remaining": "0",
                                                    "X-RateLimit-Reset": "1704110100",
                                                    "Retry-After": "30",
                                                },
                                                "duration_ms": 5.67,
                                                "error": None,
                                            },
                                        ],
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "rate_limiting_disabled": {
                                    "summary": "Rate limiting disabled",
                                    "description": "Example response when rate limiting is disabled",
                                    "value": {
                                        "rate_limiting_enabled": False,
                                        "redis_available": True,
                                        "test_requests_sent": 25,
                                        "requests_allowed": 25,
                                        "requests_blocked": 0,
                                        "first_block_at_request": None,
                                        "total_test_duration_ms": 987.65,
                                        "results": [
                                            {
                                                "request_number": 1,
                                                "allowed": True,
                                                "status_code": 200,
                                                "headers": {},
                                                "duration_ms": 15.23,
                                                "error": None,
                                            },
                                        ],
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def test_rate_limiting_endpoint(
            request: Request,
            *,
            num_requests: int = Query(
                default=25,
                ge=1,
                le=200,
                description="Number of test requests to send (1-200)",
                examples=[25, 50, 100],
            ),
        ) -> RateLimitTestResponse:
            """Test Rate Limiting Endpoint.

            Arguments:
                request (Request): Incoming request for client identification.
                num_requests (int): Number of test requests to send (default: 65).

            Returns:
                RateLimitTestResponse: Rate limiting test results.

            Raises:
                HTTPException: If test fails.
            """

            return await self.test_rate_limiting(request, num_requests)

    async def get_rate_limit_status(self, request: Request) -> RateLimitStatusResponse:
        """Get Current Rate Limiting Status And Configuration.

        Arguments:
            request (Request): Incoming request for client identification.

        Returns:
            RateLimitStatusResponse: Rate limiting status and configuration.

        Raises:
            HTTPException: If status check fails.
        """

        try:
            self._logger.info(msg="Getting rate limiting status")

            config = RateLimitConfig(
                enabled=settings.rate_limit_enabled,
                requests_per_minute=settings.rate_limit_requests_per_minute,
                burst_size=settings.rate_limit_burst_size,
                window_size=settings.rate_limit_window_size,
                redis_key_prefix=settings.rate_limit_redis_key_prefix,
                redis_key_expiry=settings.rate_limit_redis_key_expiry,
                exempt_ips=settings.rate_limit_exempt_ips,
                header_enabled=settings.rate_limit_header_enabled,
                retry_after_header=settings.rate_limit_retry_after_header,
            )

            redis_available = False
            current_status = None

            if settings.redis_enabled:
                try:
                    redis_adapter: RedisAdapter = await get_redis_adapter()
                    redis_available: bool = redis_adapter.is_connected

                    if redis_available and settings.rate_limit_enabled:
                        current_status: RateLimitStatus = await self._get_current_rate_limit_status(request)

                except Exception as exc:
                    self._logger.warning(
                        msg=f"Failed to check Redis availability: {exc!s}",
                        extra={"exception_type": type(exc).__name__},
                    )

            status_response = RateLimitStatusResponse(
                rate_limiting_enabled=settings.rate_limit_enabled,
                redis_available=redis_available,
                config=config,
                current_status=current_status,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Rate limiting status retrieved successfully",
                extra={
                    "rate_limiting_enabled": settings.rate_limit_enabled,
                    "redis_available": redis_available,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get rate limiting status: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve rate limiting status",
            ) from exc

        else:
            return status_response

    async def test_rate_limiting(self, request: Request, num_requests: int) -> RateLimitTestResponse:
        """Test Rate Limiting Functionality With Multiple Requests.

        Arguments:
            request (Request): Incoming request for client identification.
            num_requests (int): Number of test requests to send.

        Returns:
            RateLimitTestResponse: Rate limiting test results.

        Raises:
            HTTPException: If test fails.
        """

        try:
            self._logger.info(
                msg="Starting rate limiting test",
                extra={"num_requests": num_requests},
            )

            redis_available = False
            if settings.redis_enabled:
                try:
                    redis_adapter: RedisAdapter = await get_redis_adapter()
                    redis_available: bool = redis_adapter.is_connected
                except Exception as exc:
                    self._logger.warning(
                        msg=f"Redis not available for rate limiting test: {exc!s}",
                        extra={"exception_type": type(exc).__name__},
                    )

            start_time: int | float = time.time()
            results: list[RateLimitTestResult] = await self._perform_rate_limit_test(request, num_requests)
            total_duration: int | float = (time.time() - start_time) * 1000

            requests_allowed: int = sum(1 for result in results if result.allowed)
            requests_blocked: int = len(results) - requests_allowed

            first_block_at_request = None
            for result in results:
                if not result.allowed:
                    first_block_at_request: int = result.request_number
                    break

            test_response = RateLimitTestResponse(
                rate_limiting_enabled=settings.rate_limit_enabled,
                redis_available=redis_available,
                test_requests_sent=len(results),
                requests_allowed=requests_allowed,
                requests_blocked=requests_blocked,
                first_block_at_request=first_block_at_request,
                total_test_duration_ms=round(number=total_duration, ndigits=2),
                results=results,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Rate limiting test completed",
                extra={
                    "test_requests_sent": len(results),
                    "requests_allowed": requests_allowed,
                    "requests_blocked": requests_blocked,
                    "total_duration_ms": round(number=total_duration, ndigits=2),
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to test rate limiting: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to test rate limiting",
            ) from exc

        else:
            return test_response

    def _get_client_ip(self, request: Request) -> str:
        """Get Client IP Address From Request.

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
        """Get Unique Client Identifier.

        Arguments:
            request (Request): Incoming request.

        Returns:
            str: Unique client identifier hash.

        Raises:
            None
        """

        client_ip: str = self._get_client_ip(request)
        user_agent: str = request.headers.get("user-agent", default="")

        identifier_string = f"{client_ip}:{user_agent}"
        return hashlib.sha256(data=identifier_string.encode()).hexdigest()[:16]

    def _get_rate_limit_key(self, client_id: str) -> str:
        """Generate Redis Key For Rate Limiting.

        Arguments:
            client_id (str): Client identifier.

        Returns:
            str: Redis key for rate limiting.

        Raises:
            None
        """

        current_window: int = int(time.time()) // settings.rate_limit_window_size
        return f"{settings.rate_limit_redis_key_prefix}:{client_id}:{current_window}"

    async def _get_current_rate_limit_status(self, request: Request) -> RateLimitStatus:
        """Get Current Rate Limit Status For Client.

        Arguments:
            request (Request): Incoming request.

        Returns:
            RateLimitStatus: Current rate limit status.

        Raises:
            Exception: If Redis operation fails.
        """

        client_ip: str = self._get_client_ip(request)
        client_id: str = self._get_client_identifier(request)
        rate_limit_key: str = self._get_rate_limit_key(client_id)

        redis_adapter: RedisAdapter = await get_redis_adapter()

        current_count_str: str | None = await redis_adapter.get(key=rate_limit_key)
        current_count: int = int(current_count_str) if current_count_str else 0

        current_window: int = int(time.time()) // settings.rate_limit_window_size
        reset_time: datetime = datetime.fromtimestamp(
            timestamp=(current_window + 1) * settings.rate_limit_window_size,
            tz=UTC,
        )
        window_start: datetime = datetime.fromtimestamp(
            timestamp=current_window * settings.rate_limit_window_size,
            tz=UTC,
        )

        remaining: int = max(0, settings.rate_limit_requests_per_minute - current_count)
        is_exempt: bool = client_ip in settings.rate_limit_exempt_ips

        return RateLimitStatus(
            client_id=client_id,
            client_ip=client_ip,
            current_count=current_count,
            limit=settings.rate_limit_requests_per_minute,
            remaining=remaining,
            reset_time=reset_time,
            is_exempt=is_exempt,
            window_start=window_start,
        )

    async def _perform_rate_limit_test(self, request: Request, num_requests: int) -> list[RateLimitTestResult]:
        """Perform Rate Limiting Test With Multiple Requests Using Concurrent Processing.

        Arguments:
            request (Request): Incoming request for base URL.
            num_requests (int): Number of test requests to send.

        Returns:
            list[RateLimitTestResult]: List of test results.

        Raises:
            None
        """

        base_url = f"{request.url.scheme}://{request.url.netloc}"
        test_endpoint = f"{base_url}/api/v1/health/"

        semaphore = asyncio.Semaphore(value=5)

        async def make_single_request(request_number: int, client: httpx.AsyncClient) -> RateLimitTestResult:
            """Make a single HTTP request with timing and error handling.

            Arguments:
                request_number (int): Request number in sequence.
                client (httpx.AsyncClient): HTTP client instance.

            Returns:
                RateLimitTestResult: Result of the individual request.

            Raises:
                None
            """

            async with semaphore:
                await asyncio.sleep(0.05)
                start_time: float = time.time()

                try:
                    response: httpx.Response = await client.get(url=test_endpoint)
                    duration: float = (time.time() - start_time) * 1000
                    duration: float | int = max(0.0, duration)

                    headers: dict = dict(response.headers)
                    rate_limit_headers: dict = {
                        k: v for k, v in headers.items() if k.lower().startswith(("x-ratelimit", "retry-after"))
                    }

                    return RateLimitTestResult(
                        request_number=request_number,
                        allowed=response.status_code != 429,  # noqa: PLR2004
                        status_code=response.status_code,
                        headers=rate_limit_headers,
                        duration_ms=round(number=duration, ndigits=2),
                        error=None,
                    )

                except Exception as exc:
                    duration: float = (time.time() - start_time) * 1000
                    duration: float | int = max(0.0, duration)

                    error_message = str(exc) if str(exc) else f"{type(exc).__name__}"
                    if not error_message or error_message == type(exc).__name__:
                        error_message = f"{type(exc).__name__}: Unknown error occurred"

                    return RateLimitTestResult(
                        request_number=request_number,
                        allowed=False,
                        status_code=0,
                        headers={},
                        duration_ms=round(number=duration, ndigits=2),
                        error=f"Request failed: {error_message}",
                    )

        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks: list[Coroutine] = [
                make_single_request(request_number=i, client=client) for i in range(1, num_requests + 1)
            ]

            results: list[RateLimitTestResult] = await asyncio.gather(*tasks, return_exceptions=False)
            results.sort(key=lambda x: x.request_number)

        return results


rate_limit_controller: RateLimitController = RateLimitController()


__all__: list[str] = ["RateLimitController", "rate_limit_controller"]
