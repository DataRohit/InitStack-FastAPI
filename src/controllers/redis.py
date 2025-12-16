import time
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from config.adapters.redis import get_redis_adapter
from config.logger import get_logger
from config.settings import settings
from src.models.base import ErrorResponse
from src.models.redis import RedisConnectionInfo
from src.models.redis import RedisPoolStats
from src.models.redis import RedisServerInfo
from src.models.redis import RedisStatusResponse
from src.models.redis import RedisTestOperation
from src.models.redis import RedisTestResponse

if TYPE_CHECKING:
    import logging

    from config.adapters.redis import RedisAdapter


class RedisController:
    """Redis Management Controller For Database Operations Testing.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for Redis operations.
        router (APIRouter): FastAPI router for Redis endpoints.

    Properties:
        None

    Methods:
        get_redis_status: Get Redis connection and server status.
        test_redis_operations: Test various Redis operations.
        _setup_routes: Setup FastAPI routes for Redis endpoints.
        _check_redis_enabled: Check if Redis is enabled and available.
        _perform_test_operation: Perform individual Redis test operation.
    """

    def __init__(self) -> None:
        """Initialize Redis Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.redis")
        self.router: APIRouter = APIRouter(prefix="/redis", tags=["Redis"])
        self._setup_routes()

        self._logger.info(msg="Redis controller initialized")

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For Redis Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.get(
            path="/status",
            response_model=RedisStatusResponse,
            status_code=status.HTTP_200_OK,
            summary="Get Redis Status",
            description="Get comprehensive Redis connection status, pool statistics, and server information.",
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Redis is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "redis_disabled": {
                                    "summary": "Redis disabled",
                                    "description": "Example response when Redis is disabled in configuration",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Redis is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "redis_unavailable": {
                                    "summary": "Redis unavailable",
                                    "description": "Example response when Redis service is unavailable",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Redis service is temporarily unavailable",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during Redis status check",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "redis_status_error": {
                                    "summary": "Redis status check error",
                                    "description": "Example response when Redis status check encounters an internal error",  # noqa: E501
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
                    "description": "Redis status retrieved successfully",
                    "model": RedisStatusResponse,
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
                                "redis_connected": {
                                    "summary": "Redis connected",
                                    "description": "Example response when Redis is connected and healthy",
                                    "value": {
                                        "redis_enabled": True,
                                        "redis_connected": True,
                                        "connection_info": {
                                            "host": "initstack-redis-service",
                                            "port": 6379,
                                            "database": 0,
                                            "ssl_enabled": False,
                                            "max_connections": 50,
                                            "connection_timeout": 5,
                                        },
                                        "pool_stats": {
                                            "status": "initialized",
                                            "max_connections": 50,
                                            "available_connections": 48,
                                            "in_use_connections": 2,
                                            "created_connections": 5,
                                        },
                                        "server_info": {
                                            "redis_version": "8.4.0",
                                            "redis_mode": "standalone",
                                            "connected_clients": 3,
                                            "used_memory_human": "2.45M",
                                            "total_commands_processed": 1247,
                                            "keyspace_hits": 89,
                                            "keyspace_misses": 12,
                                            "uptime_in_seconds": 3600,
                                        },
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "redis_disconnected": {
                                    "summary": "Redis disconnected",
                                    "description": "Example response when Redis is not connected",
                                    "value": {
                                        "redis_enabled": True,
                                        "redis_connected": False,
                                        "connection_info": {
                                            "host": "initstack-redis-service",
                                            "port": 6379,
                                            "database": 0,
                                            "ssl_enabled": False,
                                            "max_connections": 50,
                                            "connection_timeout": 5,
                                        },
                                        "pool_stats": None,
                                        "server_info": None,
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_redis_status_endpoint() -> RedisStatusResponse:
            """Get Redis Status Endpoint.

            Arguments:
                None

            Returns:
                RedisStatusResponse: Redis connection and server status information.

            Raises:
                HTTPException: If Redis is not available or status check fails.
            """

            return await self.get_redis_status()

        @self.router.post(
            path="/test",
            response_model=RedisTestResponse,
            status_code=status.HTTP_200_OK,
            summary="Test Redis Operations",
            description="Perform comprehensive Redis operations testing including basic operations, data structures, and performance metrics.",  # noqa: E501
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Redis is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "redis_disabled": {
                                    "summary": "Redis disabled",
                                    "description": "Example response when Redis is disabled for operations test",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Redis is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "redis_connection_failed": {
                                    "summary": "Redis connection failed",
                                    "description": "Example response when Redis connection cannot be established",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Redis connection failed",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during Redis operations test",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "redis_test_error": {
                                    "summary": "Redis operations test error",
                                    "description": "Example response when Redis operations test encounters an internal error",  # noqa: E501
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
                    "description": "Redis operations test completed successfully",
                    "model": RedisTestResponse,
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
                                "all_operations_successful": {
                                    "summary": "All operations successful",
                                    "description": "Example response when all Redis operations succeed",
                                    "value": {
                                        "redis_connected": True,
                                        "operations_tested": 12,
                                        "operations_successful": 12,
                                        "operations_failed": 0,
                                        "total_duration_ms": 45.67,
                                        "operations": [
                                            {
                                                "operation": "ping",
                                                "success": True,
                                                "duration_ms": 1.23,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "set_key",
                                                "success": True,
                                                "duration_ms": 2.45,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "get_key",
                                                "success": True,
                                                "duration_ms": 1.89,
                                                "result": "test_value_12345",
                                                "error": None,
                                            },
                                        ],
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "some_operations_failed": {
                                    "summary": "Some operations failed",
                                    "description": "Example response when some Redis operations fail",
                                    "value": {
                                        "redis_connected": True,
                                        "operations_tested": 12,
                                        "operations_successful": 10,
                                        "operations_failed": 2,
                                        "total_duration_ms": 52.34,
                                        "operations": [
                                            {
                                                "operation": "ping",
                                                "success": True,
                                                "duration_ms": 1.23,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "invalid_operation",
                                                "success": False,
                                                "duration_ms": 0.45,
                                                "result": None,
                                                "error": "Redis operation failed: invalid command",
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
        async def test_redis_operations_endpoint() -> RedisTestResponse:
            """Test Redis Operations Endpoint.

            Arguments:
                None

            Returns:
                RedisTestResponse: Redis operations test results.

            Raises:
                HTTPException: If Redis is not available or test fails.
            """

            return await self.test_redis_operations()

    async def get_redis_status(self) -> RedisStatusResponse:
        """Get Redis Connection And Server Status.

        Arguments:
            None

        Returns:
            RedisStatusResponse: Redis status information.

        Raises:
            HTTPException: If Redis is not available or status check fails.
        """

        try:
            self._logger.info(msg="Getting Redis status")

            if not settings.redis_enabled:
                self._logger.warning(msg="Redis is not enabled")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Redis is not enabled",
                )

            connection_info = RedisConnectionInfo(
                host=settings.redis_host,
                port=settings.redis_port,
                database=settings.redis_database,
                ssl_enabled=settings.redis_ssl,
                max_connections=settings.redis_max_connections,
                connection_timeout=settings.redis_connection_timeout,
            )

            redis_adapter: RedisAdapter = await get_redis_adapter()
            redis_connected: bool = redis_adapter.is_connected

            pool_stats = None
            server_info = None

            if redis_connected:
                try:
                    pool_stats_data: dict[str, Any] = redis_adapter.pool_stats
                    pool_stats = RedisPoolStats(**pool_stats_data)

                    server_info_data: dict[str, Any] = await redis_adapter.get_info()
                    server_info = RedisServerInfo(
                        redis_version=server_info_data.get("redis_version"),
                        redis_mode=server_info_data.get("redis_mode"),
                        connected_clients=server_info_data.get("connected_clients"),
                        used_memory_human=server_info_data.get("used_memory_human"),
                        total_commands_processed=server_info_data.get("total_commands_processed"),
                        keyspace_hits=server_info_data.get("keyspace_hits"),
                        keyspace_misses=server_info_data.get("keyspace_misses"),
                        uptime_in_seconds=server_info_data.get("uptime_in_seconds"),
                    )

                except Exception as exc:
                    self._logger.warning(
                        msg=f"Failed to get Redis server info: {exc!s}",
                        extra={"exception_type": type(exc).__name__},
                    )

            status_response = RedisStatusResponse(
                redis_enabled=settings.redis_enabled,
                redis_connected=redis_connected,
                connection_info=connection_info,
                pool_stats=pool_stats,
                server_info=server_info,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Redis status retrieved successfully",
                extra={
                    "redis_enabled": settings.redis_enabled,
                    "redis_connected": redis_connected,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get Redis status: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Redis status",
            ) from exc

        else:
            return status_response

    async def test_redis_operations(self) -> RedisTestResponse:
        """Test Various Redis Operations.

        Arguments:
            None

        Returns:
            RedisTestResponse: Redis operations test results.

        Raises:
            HTTPException: If Redis is not available or test fails.
        """

        try:
            self._logger.info(msg="Starting Redis operations test")

            await self._check_redis_enabled()

            redis_adapter: RedisAdapter = await get_redis_adapter()

            if not redis_adapter.is_connected:
                await redis_adapter.connect()

            start_time: int | float = time.time()
            operations: list[Any] = []

            test_operations: list[tuple[str, Any]] = [
                ("ping", lambda: redis_adapter.client.ping()),
                ("set_key", lambda: redis_adapter.set(key="test:key:12345", value="test_value_12345", ex=300)),
                ("get_key", lambda: redis_adapter.get(key="test:key:12345")),
                ("exists_key", lambda: redis_adapter.exists("test:key:12345")),
                ("ttl_key", lambda: redis_adapter.ttl(key="test:key:12345")),
                ("incr_counter", lambda: redis_adapter.incr(key="test:counter:12345")),
                ("decr_counter", lambda: redis_adapter.decr(key="test:counter:12345")),
                ("hset_hash", lambda: redis_adapter.hset(name="test:hash:12345", key="field1", value="value1")),
                ("hget_hash", lambda: redis_adapter.hget(name="test:hash:12345", key="field1")),
                ("hgetall_hash", lambda: redis_adapter.hgetall(name="test:hash:12345")),
                ("delete_keys", lambda: redis_adapter.delete("test:key:12345", "test:counter:12345")),
                ("hdel_hash", lambda: redis_adapter.hdel("test:hash:12345", "field1")),
            ]

            for operation_name, operation_func in test_operations:
                operation_result: RedisTestOperation = await self._perform_test_operation(
                    operation_name,
                    operation_func,
                )
                operations.append(operation_result)

            total_duration: int | float = (time.time() - start_time) * 1000
            successful_operations: int = sum(1 for op in operations if op.success)
            failed_operations: int = len(operations) - successful_operations

            test_response = RedisTestResponse(
                redis_connected=redis_adapter.is_connected,
                operations_tested=len(operations),
                operations_successful=successful_operations,
                operations_failed=failed_operations,
                total_duration_ms=round(number=total_duration, ndigits=2),
                operations=operations,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Redis operations test completed",
                extra={
                    "operations_tested": len(operations),
                    "operations_successful": successful_operations,
                    "operations_failed": failed_operations,
                    "total_duration_ms": round(number=total_duration, ndigits=2),
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to test Redis operations: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to test Redis operations",
            ) from exc

        else:
            return test_response

    async def _check_redis_enabled(self) -> None:
        """Check If Redis Is Enabled And Available.

        Arguments:
            None

        Returns:
            None

        Raises:
            HTTPException: If Redis is not enabled.
        """

        if not settings.redis_enabled:
            self._logger.warning(msg="Redis is not enabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis is not enabled",
            )

    async def _perform_test_operation(self, operation_name: str, operation_func) -> RedisTestOperation:
        """Perform Individual Redis Test Operation.

        Arguments:
            operation_name (str): Name of the operation.
            operation_func: Function to execute the operation.

        Returns:
            RedisTestOperation: Operation test result.

        Raises:
            None
        """

        start_time: int | float = time.time()

        try:
            result: Any = await operation_func()
            duration: int | float = (time.time() - start_time) * 1000

            return RedisTestOperation(
                operation=operation_name,
                success=True,
                duration_ms=round(number=duration, ndigits=2),
                result=result,
                error=None,
            )

        except Exception as exc:
            duration: int | float = (time.time() - start_time) * 1000

            self._logger.warning(
                msg=f"Redis operation '{operation_name}' failed: {exc!s}",
                extra={
                    "operation": operation_name,
                    "exception_type": type(exc).__name__,
                },
            )

            return RedisTestOperation(
                operation=operation_name,
                success=False,
                duration_ms=round(number=duration, ndigits=2),
                result=None,
                error=f"Redis operation failed: {exc!s}",
            )


redis_controller: RedisController = RedisController()


__all__: list[str] = ["RedisController", "redis_controller"]
