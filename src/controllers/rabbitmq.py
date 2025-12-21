import time
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from aio_pika import ExchangeType
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from config.adapters.rabbitmq import get_rabbitmq_adapter
from config.logger import get_logger
from config.settings import settings
from src.schemas.base import ErrorResponse
from src.schemas.rabbitmq import RabbitMQChannelInfo
from src.schemas.rabbitmq import RabbitMQConnectionInfo
from src.schemas.rabbitmq import RabbitMQStatusResponse
from src.schemas.rabbitmq import RabbitMQTestOperation
from src.schemas.rabbitmq import RabbitMQTestResponse

if TYPE_CHECKING:
    import logging

    from config.adapters.rabbitmq import RabbitMQAdapter


class RabbitMQController:
    """RabbitMQ Management Controller For Message Broker Operations Testing.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for RabbitMQ operations.
        router (APIRouter): FastAPI router for RabbitMQ endpoints.

    Properties:
        None

    Methods:
        get_rabbitmq_status: Get RabbitMQ connection and server status.
        test_rabbitmq_operations: Test various RabbitMQ operations.
        _setup_routes: Setup FastAPI routes for RabbitMQ endpoints.
        _check_rabbitmq_enabled: Check if RabbitMQ is enabled and available.
        _perform_test_operation: Perform individual RabbitMQ test operation.
    """

    def __init__(self) -> None:
        """Initialize RabbitMQ Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.rabbitmq")
        self.router: APIRouter = APIRouter(prefix="/rabbitmq", tags=["RabbitMQ"])
        self._setup_routes()

        self._logger.info(msg="RabbitMQ controller initialized")

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For RabbitMQ Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.get(
            path="/status",
            response_model=RabbitMQStatusResponse,
            status_code=status.HTTP_200_OK,
            summary="Get RabbitMQ Status",
            description="Get comprehensive RabbitMQ connection status, channel information, and server details.",
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "RabbitMQ is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rabbitmq_disabled": {
                                    "summary": "RabbitMQ disabled",
                                    "description": "Example response when RabbitMQ is disabled in configuration",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "RabbitMQ is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "rabbitmq_unavailable": {
                                    "summary": "RabbitMQ unavailable",
                                    "description": "Example response when RabbitMQ service is unavailable",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "RabbitMQ service is temporarily unavailable",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during RabbitMQ status check",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rabbitmq_status_error": {
                                    "summary": "RabbitMQ status check error",
                                    "description": "Example response when RabbitMQ status check encounters an internal error",  # noqa: E501
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
                    "description": "RabbitMQ status retrieved successfully",
                    "model": RabbitMQStatusResponse,
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
                                "rabbitmq_connected": {
                                    "summary": "RabbitMQ connected",
                                    "description": "Example response when RabbitMQ is connected and healthy",
                                    "value": {
                                        "rabbitmq_enabled": True,
                                        "rabbitmq_connected": True,
                                        "connection_info": {
                                            "host": "initstack-rabbitmq-service",
                                            "port": 5672,
                                            "vhost": "/",
                                            "ssl_enabled": False,
                                            "connection_name": "initstack-fastapi-service",
                                            "connection_timeout": 10,
                                        },
                                        "channel_info": {
                                            "channel_number": 1,
                                            "is_closed": False,
                                            "prefetch_count": 10,
                                        },
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "rabbitmq_disconnected": {
                                    "summary": "RabbitMQ disconnected",
                                    "description": "Example response when RabbitMQ is not connected",
                                    "value": {
                                        "rabbitmq_enabled": True,
                                        "rabbitmq_connected": False,
                                        "connection_info": {
                                            "host": "initstack-rabbitmq-service",
                                            "port": 5672,
                                            "vhost": "/",
                                            "ssl_enabled": False,
                                            "connection_name": "initstack-fastapi-service",
                                            "connection_timeout": 10,
                                        },
                                        "channel_info": None,
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_rabbitmq_status_endpoint() -> RabbitMQStatusResponse:
            """Get RabbitMQ Status Endpoint.

            Arguments:
                None

            Returns:
                RabbitMQStatusResponse: RabbitMQ connection and server status information.

            Raises:
                HTTPException: If RabbitMQ is not available or status check fails.
            """

            return await self.get_rabbitmq_status()

        @self.router.post(
            path="/test",
            response_model=RabbitMQTestResponse,
            status_code=status.HTTP_200_OK,
            summary="Test RabbitMQ Operations",
            description="Perform comprehensive RabbitMQ operations testing including exchange/queue operations, message publishing, and performance metrics.",  # noqa: E501
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "RabbitMQ is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rabbitmq_disabled": {
                                    "summary": "RabbitMQ disabled",
                                    "description": "Example response when RabbitMQ is disabled for operations test",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "RabbitMQ is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "rabbitmq_connection_failed": {
                                    "summary": "RabbitMQ connection failed",
                                    "description": "Example response when RabbitMQ connection cannot be established",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "RabbitMQ connection failed",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during RabbitMQ operations test",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "rabbitmq_test_error": {
                                    "summary": "RabbitMQ operations test error",
                                    "description": "Example response when RabbitMQ operations test encounters an internal error",  # noqa: E501
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
                    "description": "RabbitMQ operations test completed successfully",
                    "model": RabbitMQTestResponse,
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
                                    "description": "Example response when all RabbitMQ operations succeed",
                                    "value": {
                                        "rabbitmq_connected": True,
                                        "operations_tested": 8,
                                        "operations_successful": 8,
                                        "operations_failed": 0,
                                        "total_duration_ms": 45.67,
                                        "operations": [
                                            {
                                                "operation": "declare_exchange",
                                                "success": True,
                                                "duration_ms": 5.23,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "declare_queue",
                                                "success": True,
                                                "duration_ms": 4.45,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "bind_queue",
                                                "success": True,
                                                "duration_ms": 3.89,
                                                "result": None,
                                                "error": None,
                                            },
                                        ],
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "some_operations_failed": {
                                    "summary": "Some operations failed",
                                    "description": "Example response when some RabbitMQ operations fail",
                                    "value": {
                                        "rabbitmq_connected": True,
                                        "operations_tested": 8,
                                        "operations_successful": 6,
                                        "operations_failed": 2,
                                        "total_duration_ms": 52.34,
                                        "operations": [
                                            {
                                                "operation": "declare_exchange",
                                                "success": True,
                                                "duration_ms": 5.23,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "invalid_operation",
                                                "success": False,
                                                "duration_ms": 0.45,
                                                "result": None,
                                                "error": "RabbitMQ operation failed: invalid operation",
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
        async def test_rabbitmq_operations_endpoint() -> RabbitMQTestResponse:
            """Test RabbitMQ Operations Endpoint.

            Arguments:
                None

            Returns:
                RabbitMQTestResponse: RabbitMQ operations test results.

            Raises:
                HTTPException: If RabbitMQ is not available or test fails.
            """

            return await self.test_rabbitmq_operations()

    async def get_rabbitmq_status(self) -> RabbitMQStatusResponse:
        """Get RabbitMQ Connection And Server Status.

        Arguments:
            None

        Returns:
            RabbitMQStatusResponse: RabbitMQ status information.

        Raises:
            HTTPException: If RabbitMQ is not available or status check fails.
        """

        try:
            self._logger.info(msg="Getting RabbitMQ status")

            if not settings.rabbitmq_enabled:
                self._logger.warning(msg="RabbitMQ is not enabled")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="RabbitMQ is not enabled",
                )

            connection_info = RabbitMQConnectionInfo(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                vhost=settings.rabbitmq_vhost,
                ssl_enabled=settings.rabbitmq_ssl,
                connection_name=settings.rabbitmq_connection_name,
                connection_timeout=settings.rabbitmq_connection_timeout,
            )

            rabbitmq_adapter: RabbitMQAdapter = await get_rabbitmq_adapter()
            rabbitmq_connected: bool = rabbitmq_adapter.is_connected

            channel_info = None

            if rabbitmq_connected:
                try:
                    conn_info_data: dict[str, Any] = await rabbitmq_adapter.get_connection_info()

                    channel_info = RabbitMQChannelInfo(
                        channel_number=conn_info_data.get("channel_number"),
                        is_closed=conn_info_data.get("channel_is_closed"),
                        prefetch_count=settings.rabbitmq_prefetch_count,
                    )

                except Exception as exc:
                    self._logger.warning(
                        msg=f"Failed to get RabbitMQ channel info: {exc!s}",
                        extra={"exception_type": type(exc).__name__},
                    )

            status_response = RabbitMQStatusResponse(
                rabbitmq_enabled=settings.rabbitmq_enabled,
                rabbitmq_connected=rabbitmq_connected,
                connection_info=connection_info,
                channel_info=channel_info,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="RabbitMQ status retrieved successfully",
                extra={
                    "rabbitmq_enabled": settings.rabbitmq_enabled,
                    "rabbitmq_connected": rabbitmq_connected,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get RabbitMQ status: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve RabbitMQ status",
            ) from exc

        else:
            return status_response

    async def test_rabbitmq_operations(self) -> RabbitMQTestResponse:
        """Test Various RabbitMQ Operations.

        Arguments:
            None

        Returns:
            RabbitMQTestResponse: RabbitMQ operations test results.

        Raises:
            HTTPException: If RabbitMQ is not available or test fails.
        """

        try:
            self._logger.info(msg="Starting RabbitMQ operations test")

            await self._check_rabbitmq_enabled()

            rabbitmq_adapter: RabbitMQAdapter = await get_rabbitmq_adapter()

            if not rabbitmq_adapter.is_connected:
                await rabbitmq_adapter.connect()

            start_time: int | float = time.time()
            operations: list[Any] = []

            test_operations: list[tuple[str, Any]] = [
                (
                    "declare_exchange",
                    lambda: rabbitmq_adapter.declare_exchange(
                        name="test_exchange_12345",
                        exchange_type=ExchangeType.DIRECT,
                        durable=True,
                    ),
                ),
                (
                    "declare_queue",
                    lambda: rabbitmq_adapter.declare_queue(name="test_queue_12345", durable=True),
                ),
                (
                    "bind_queue",
                    lambda: rabbitmq_adapter.bind_queue(
                        queue_name="test_queue_12345",
                        exchange_name="test_exchange_12345",
                        routing_key="test_key",
                    ),
                ),
                (
                    "publish_message",
                    lambda: rabbitmq_adapter.publish_message(
                        exchange_name="test_exchange_12345",
                        routing_key="test_key",
                        message_body="Test message content",
                        content_type="text/plain",
                    ),
                ),
                (
                    "get_queue_info",
                    lambda: rabbitmq_adapter.get_queue_info(queue_name="test_queue_12345"),
                ),
                (
                    "purge_queue",
                    lambda: rabbitmq_adapter.purge_queue(queue_name="test_queue_12345"),
                ),
                (
                    "delete_queue",
                    lambda: rabbitmq_adapter.delete_queue(queue_name="test_queue_12345"),
                ),
                (
                    "delete_exchange",
                    lambda: rabbitmq_adapter.delete_exchange(exchange_name="test_exchange_12345"),
                ),
            ]

            for operation_name, operation_func in test_operations:
                operation_result: RabbitMQTestOperation = await self._perform_test_operation(
                    operation_name,
                    operation_func,
                )
                operations.append(operation_result)

            total_duration: int | float = (time.time() - start_time) * 1000
            successful_operations: int = sum(1 for op in operations if op.success)
            failed_operations: int = len(operations) - successful_operations

            test_response = RabbitMQTestResponse(
                rabbitmq_connected=rabbitmq_adapter.is_connected,
                operations_tested=len(operations),
                operations_successful=successful_operations,
                operations_failed=failed_operations,
                total_duration_ms=round(number=total_duration, ndigits=2),
                operations=operations,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="RabbitMQ operations test completed",
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
                msg=f"Failed to test RabbitMQ operations: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to test RabbitMQ operations",
            ) from exc

        else:
            return test_response

    async def _check_rabbitmq_enabled(self) -> None:
        """Check If RabbitMQ Is Enabled And Available.

        Arguments:
            None

        Returns:
            None

        Raises:
            HTTPException: If RabbitMQ is not enabled.
        """

        if not settings.rabbitmq_enabled:
            self._logger.warning(msg="RabbitMQ is not enabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RabbitMQ is not enabled",
            )

    async def _perform_test_operation(self, operation_name: str, operation_func) -> RabbitMQTestOperation:
        """Perform Individual RabbitMQ Test Operation.

        Arguments:
            operation_name (str): Name of the operation.
            operation_func: Function to execute the operation.

        Returns:
            RabbitMQTestOperation: Operation test result.

        Raises:
            None
        """

        start_time: int | float = time.time()

        try:
            result: Any = await operation_func()
            duration: int | float = (time.time() - start_time) * 1000

            return RabbitMQTestOperation(
                operation=operation_name,
                success=True,
                duration_ms=round(number=duration, ndigits=2),
                result=str(result)
                if result is not None and not isinstance(result, (bool, int, float, str))
                else result,
                error=None,
            )

        except Exception as exc:
            duration: int | float = (time.time() - start_time) * 1000

            self._logger.warning(
                msg=f"RabbitMQ operation '{operation_name}' failed: {exc!s}",
                extra={
                    "operation": operation_name,
                    "exception_type": type(exc).__name__,
                },
            )

            return RabbitMQTestOperation(
                operation=operation_name,
                success=False,
                duration_ms=round(number=duration, ndigits=2),
                result=None,
                error=f"RabbitMQ operation failed: {exc!s}",
            )


rabbitmq_controller: RabbitMQController = RabbitMQController()


__all__: list[str] = ["RabbitMQController", "rabbitmq_controller"]
