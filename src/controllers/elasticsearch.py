import time
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from config.adapters.elasticsearch import get_elasticsearch_adapter
from config.logger import get_logger
from config.settings import settings
from src.schemas.base import ErrorResponse
from src.schemas.elasticsearch import ElasticsearchClusterInfo
from src.schemas.elasticsearch import ElasticsearchConnectionInfo
from src.schemas.elasticsearch import ElasticsearchStatusResponse
from src.schemas.elasticsearch import ElasticsearchTestOperation
from src.schemas.elasticsearch import ElasticsearchTestResponse

if TYPE_CHECKING:
    import logging

    from config.adapters.elasticsearch import ElasticsearchAdapter


class ElasticsearchController:
    """Elasticsearch Management Controller For Search Engine Operations Testing.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for Elasticsearch operations.
        router (APIRouter): FastAPI router for Elasticsearch endpoints.

    Properties:
        None

    Methods:
        get_elasticsearch_status: Get Elasticsearch connection and cluster status.
        test_elasticsearch_operations: Test various Elasticsearch operations.
        _setup_routes: Setup FastAPI routes for Elasticsearch endpoints.
        _check_elasticsearch_enabled: Check if Elasticsearch is enabled and available.
        _perform_test_operation: Perform individual Elasticsearch test operation.
    """

    def __init__(self) -> None:
        """Initialize Elasticsearch Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.elasticsearch")
        self.router: APIRouter = APIRouter(prefix="/elasticsearch", tags=["Elasticsearch"])
        self._setup_routes()

        self._logger.info(msg="Elasticsearch controller initialized")

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For Elasticsearch Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.get(
            path="/status",
            response_model=ElasticsearchStatusResponse,
            status_code=status.HTTP_200_OK,
            summary="Get Elasticsearch Status",
            description="Get comprehensive Elasticsearch connection status, cluster health, and node information.",
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Elasticsearch is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "elasticsearch_disabled": {
                                    "summary": "Elasticsearch disabled",
                                    "description": "Example response when Elasticsearch is disabled in configuration",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Elasticsearch is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "elasticsearch_unavailable": {
                                    "summary": "Elasticsearch unavailable",
                                    "description": "Example response when Elasticsearch service is unavailable",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Elasticsearch service is temporarily unavailable",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during Elasticsearch status check",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "elasticsearch_status_error": {
                                    "summary": "Elasticsearch status check error",
                                    "description": "Example response when Elasticsearch status check encounters an internal error",  # noqa: E501
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
                    "description": "Elasticsearch status retrieved successfully",
                    "model": ElasticsearchStatusResponse,
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
                                "elasticsearch_connected": {
                                    "summary": "Elasticsearch connected",
                                    "description": "Example response when Elasticsearch is connected and healthy",
                                    "value": {
                                        "elasticsearch_enabled": True,
                                        "elasticsearch_connected": True,
                                        "connection_info": {
                                            "hosts": ["http://initstack-elasticsearch-service:9200"],
                                            "username": "elastic",
                                            "ssl_enabled": False,
                                            "connection_timeout": 10,
                                            "request_timeout": 30,
                                        },
                                        "cluster_info": {
                                            "name": "initstack-cluster",
                                            "version": "9.2.0",
                                            "status": "green",
                                            "number_of_nodes": 1,
                                            "active_shards": 0,
                                        },
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "elasticsearch_disconnected": {
                                    "summary": "Elasticsearch disconnected",
                                    "description": "Example response when Elasticsearch is not connected",
                                    "value": {
                                        "elasticsearch_enabled": True,
                                        "elasticsearch_connected": False,
                                        "connection_info": {
                                            "hosts": ["http://initstack-elasticsearch-service:9200"],
                                            "username": "elastic",
                                            "ssl_enabled": False,
                                            "connection_timeout": 10,
                                            "request_timeout": 30,
                                        },
                                        "cluster_info": None,
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_elasticsearch_status_endpoint() -> ElasticsearchStatusResponse:
            """Get Elasticsearch Status Endpoint.

            Arguments:
                None

            Returns:
                ElasticsearchStatusResponse: Elasticsearch connection and cluster status information.

            Raises:
                HTTPException: If Elasticsearch is not available or status check fails.
            """

            return await self.get_elasticsearch_status()

        @self.router.post(
            path="/test",
            response_model=ElasticsearchTestResponse,
            status_code=status.HTTP_200_OK,
            summary="Test Elasticsearch Operations",
            description="Perform comprehensive Elasticsearch operations testing including index management, document operations, search, and performance metrics.",  # noqa: E501
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Elasticsearch is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "elasticsearch_disabled": {
                                    "summary": "Elasticsearch disabled",
                                    "description": "Example response when Elasticsearch is disabled for operations test",  # noqa: E501
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Elasticsearch is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "elasticsearch_connection_failed": {
                                    "summary": "Elasticsearch connection failed",
                                    "description": "Example response when Elasticsearch connection cannot be established",  # noqa: E501
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Elasticsearch connection failed",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during Elasticsearch operations test",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "elasticsearch_test_error": {
                                    "summary": "Elasticsearch operations test error",
                                    "description": "Example response when Elasticsearch operations test encounters an internal error",  # noqa: E501
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
                    "description": "Elasticsearch operations test completed successfully",
                    "model": ElasticsearchTestResponse,
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
                                    "description": "Example response when all Elasticsearch operations succeed",
                                    "value": {
                                        "elasticsearch_connected": True,
                                        "operations_tested": 7,
                                        "operations_successful": 7,
                                        "operations_failed": 0,
                                        "total_duration_ms": 125.45,
                                        "operations": [
                                            {
                                                "operation": "create_index",
                                                "success": True,
                                                "duration_ms": 15.23,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "index_document",
                                                "success": True,
                                                "duration_ms": 8.45,
                                                "result": "doc_id_123",
                                                "error": None,
                                            },
                                            {
                                                "operation": "search",
                                                "success": True,
                                                "duration_ms": 12.89,
                                                "result": 1,
                                                "error": None,
                                            },
                                        ],
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "some_operations_failed": {
                                    "summary": "Some operations failed",
                                    "description": "Example response when some Elasticsearch operations fail",
                                    "value": {
                                        "elasticsearch_connected": True,
                                        "operations_tested": 7,
                                        "operations_successful": 5,
                                        "operations_failed": 2,
                                        "total_duration_ms": 98.34,
                                        "operations": [
                                            {
                                                "operation": "create_index",
                                                "success": True,
                                                "duration_ms": 15.23,
                                                "result": True,
                                                "error": None,
                                            },
                                            {
                                                "operation": "invalid_operation",
                                                "success": False,
                                                "duration_ms": 0.45,
                                                "result": None,
                                                "error": "Elasticsearch operation failed: invalid operation",
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
        async def test_elasticsearch_operations_endpoint() -> ElasticsearchTestResponse:
            """Test Elasticsearch Operations Endpoint.

            Arguments:
                None

            Returns:
                ElasticsearchTestResponse: Elasticsearch operations test results.

            Raises:
                HTTPException: If Elasticsearch is not available or test fails.
            """

            return await self.test_elasticsearch_operations()

    async def get_elasticsearch_status(self) -> ElasticsearchStatusResponse:
        """Get Elasticsearch Connection And Cluster Status.

        Arguments:
            None

        Returns:
            ElasticsearchStatusResponse: Elasticsearch status information.

        Raises:
            HTTPException: If Elasticsearch is not available or status check fails.
        """

        try:
            self._logger.info(msg="Getting Elasticsearch status")

            if not settings.elasticsearch_enabled:
                self._logger.warning(msg="Elasticsearch is not enabled")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Elasticsearch is not enabled",
                )

            connection_info = ElasticsearchConnectionInfo(
                hosts=settings.elasticsearch_hosts,
                username=settings.elasticsearch_username,
                ssl_enabled=settings.elasticsearch_ssl,
                connection_timeout=settings.elasticsearch_connection_timeout,
                request_timeout=settings.elasticsearch_request_timeout,
            )

            elasticsearch_adapter: ElasticsearchAdapter = await get_elasticsearch_adapter()
            elasticsearch_connected: bool = elasticsearch_adapter.is_connected

            cluster_info = None

            if elasticsearch_connected:
                try:
                    cluster_data: dict[str, Any] = await elasticsearch_adapter.get_cluster_info()

                    cluster_info = ElasticsearchClusterInfo(
                        name=cluster_data.get("name"),
                        version=cluster_data.get("version"),
                        status=cluster_data.get("status"),
                        number_of_nodes=cluster_data.get("number_of_nodes"),
                        active_shards=cluster_data.get("active_shards"),
                    )

                except Exception as exc:
                    self._logger.warning(
                        msg=f"Failed to get Elasticsearch cluster info: {exc!s}",
                        extra={"exception_type": type(exc).__name__},
                    )

            status_response = ElasticsearchStatusResponse(
                elasticsearch_enabled=settings.elasticsearch_enabled,
                elasticsearch_connected=elasticsearch_connected,
                connection_info=connection_info,
                cluster_info=cluster_info,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Elasticsearch status retrieved successfully",
                extra={
                    "elasticsearch_enabled": settings.elasticsearch_enabled,
                    "elasticsearch_connected": elasticsearch_connected,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get Elasticsearch status: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Elasticsearch status",
            ) from exc

        else:
            return status_response

    async def test_elasticsearch_operations(self) -> ElasticsearchTestResponse:
        """Test Various Elasticsearch Operations.

        Arguments:
            None

        Returns:
            ElasticsearchTestResponse: Elasticsearch operations test results.

        Raises:
            HTTPException: If Elasticsearch is not available or test fails.
        """

        try:
            self._logger.info(msg="Starting Elasticsearch operations test")

            await self._check_elasticsearch_enabled()

            elasticsearch_adapter: ElasticsearchAdapter = await get_elasticsearch_adapter()

            if not elasticsearch_adapter.is_connected:
                await elasticsearch_adapter.connect()

            start_time: int | float = time.time()
            operations: list[Any] = []

            test_index: str = "test_index_12345"
            test_doc_id: str = "test_doc_12345"

            test_operations: list[tuple[str, Any]] = [
                (
                    "create_index",
                    lambda: elasticsearch_adapter.create_index(index_name=test_index),
                ),
                (
                    "index_document",
                    lambda: elasticsearch_adapter.index_document(
                        index_name=test_index,
                        document={
                            "title": "Test Document",
                            "content": "Test content",
                            "timestamp": datetime.now(tz=UTC).isoformat(),
                        },
                        document_id=test_doc_id,
                    ),
                ),
                (
                    "get_document",
                    lambda: elasticsearch_adapter.get_document(index_name=test_index, document_id=test_doc_id),
                ),
                (
                    "search",
                    lambda: elasticsearch_adapter.search(
                        index_name=test_index,
                        query={"match": {"title": "Test"}},
                        size=10,
                    ),
                ),
                (
                    "update_document",
                    lambda: elasticsearch_adapter.update_document(
                        index_name=test_index,
                        document_id=test_doc_id,
                        document={"content": "Updated content"},
                    ),
                ),
                (
                    "delete_document",
                    lambda: elasticsearch_adapter.delete_document(index_name=test_index, document_id=test_doc_id),
                ),
                (
                    "delete_index",
                    lambda: elasticsearch_adapter.delete_index(index_name=test_index),
                ),
            ]

            for operation_name, operation_func in test_operations:
                operation_result: ElasticsearchTestOperation = await self._perform_test_operation(
                    operation_name,
                    operation_func,
                )
                operations.append(operation_result)

            total_duration: int | float = (time.time() - start_time) * 1000
            successful_operations: int = sum(1 for op in operations if op.success)
            failed_operations: int = len(operations) - successful_operations

            test_response = ElasticsearchTestResponse(
                elasticsearch_connected=elasticsearch_adapter.is_connected,
                operations_tested=len(operations),
                operations_successful=successful_operations,
                operations_failed=failed_operations,
                total_duration_ms=round(number=total_duration, ndigits=2),
                operations=operations,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Elasticsearch operations test completed",
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
                msg=f"Failed to test Elasticsearch operations: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to test Elasticsearch operations",
            ) from exc

        else:
            return test_response

    async def _check_elasticsearch_enabled(self) -> None:
        """Check If Elasticsearch Is Enabled And Available.

        Arguments:
            None

        Returns:
            None

        Raises:
            HTTPException: If Elasticsearch is not enabled.
        """

        if not settings.elasticsearch_enabled:
            self._logger.warning(msg="Elasticsearch is not enabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Elasticsearch is not enabled",
            )

    async def _perform_test_operation(self, operation_name: str, operation_func) -> ElasticsearchTestOperation:
        """Perform Individual Elasticsearch Test Operation.

        Arguments:
            operation_name (str): Name of the operation.
            operation_func: Function to execute the operation.

        Returns:
            ElasticsearchTestOperation: Operation test result.

        Raises:
            None
        """

        start_time: int | float = time.time()

        try:
            result: Any = await operation_func()
            duration: int | float = (time.time() - start_time) * 1000

            result_value: Any = result
            if result is not None and not isinstance(result, (bool, int, float, str)):
                if isinstance(result, dict):
                    result_value = (
                        result.get("hits", {})
                        .get("total", {})
                        .get("value", len(result.get("hits", {}).get("hits", [])))
                    )
                else:
                    result_value = str(object=result)

            return ElasticsearchTestOperation(
                operation=operation_name,
                success=True,
                duration_ms=round(number=duration, ndigits=2),
                result=result_value,
                error=None,
            )

        except Exception as exc:
            duration: int | float = (time.time() - start_time) * 1000

            self._logger.warning(
                msg=f"Elasticsearch operation '{operation_name}' failed: {exc!s}",
                extra={
                    "operation": operation_name,
                    "exception_type": type(exc).__name__,
                },
            )

            return ElasticsearchTestOperation(
                operation=operation_name,
                success=False,
                duration_ms=round(number=duration, ndigits=2),
                result=None,
                error=f"Elasticsearch operation failed: {exc!s}",
            )


elasticsearch_controller: ElasticsearchController = ElasticsearchController()


__all__: list[str] = ["ElasticsearchController", "elasticsearch_controller"]
