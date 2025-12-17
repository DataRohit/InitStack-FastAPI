from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from config.adapters.consul import get_consul_adapter
from config.logger import get_logger
from config.settings import settings
from src.schemas.base import ErrorResponse
from src.schemas.consul import ConsulServiceDiscoveryResponse
from src.schemas.consul import ConsulServiceHealth
from src.schemas.consul import ConsulServiceInstance
from src.schemas.consul import ConsulStatusResponse

if TYPE_CHECKING:
    import logging

    from config.adapters.consul import ConsulAdapter


class ConsulController:
    """Consul Management Controller For Service Discovery Operations.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for Consul operations.
        router (APIRouter): FastAPI router for Consul endpoints.

    Properties:
        None

    Methods:
        get_consul_status: Get Consul cluster and service status.
        discover_service: Discover services by name.
        get_service_health: Get service health information.
        _setup_routes: Setup FastAPI routes for Consul endpoints.
        _check_consul_enabled: Check if Consul is enabled and available.
    """

    def __init__(self) -> None:
        """Initialize Consul Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.consul")
        self.router: APIRouter = APIRouter(prefix="/consul", tags=["Consul"])
        self._setup_routes()

        self._logger.info(msg="Consul controller initialized")

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For Consul Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.get(
            path="/status",
            response_model=ConsulStatusResponse,
            status_code=status.HTTP_200_OK,
            summary="Get Consul Status",
            description="Get comprehensive Consul cluster status and current service registration information.",
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Consul is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "consul_disabled": {
                                    "summary": "Consul disabled",
                                    "description": "Example response when Consul is disabled in configuration",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Consul service discovery is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during Consul status check",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "consul_error": {
                                    "summary": "Consul status check error",
                                    "description": "Example response when Consul status check fails",
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
                    "description": "Consul status retrieved successfully",
                    "model": ConsulStatusResponse,
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
                                "healthy_consul": {
                                    "summary": "Healthy Consul cluster",
                                    "description": "Example response when Consul is healthy and service is registered",
                                    "value": {
                                        "consul_healthy": True,
                                        "leader": "172.18.0.10:8300",
                                        "peers_count": 1,
                                        "service_registered": True,
                                        "service_id": "initstack-fastapi-service-172.18.0.19-8000-402f4c44",
                                        "service_name": "initstack-fastapi-service",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "unhealthy_consul": {
                                    "summary": "Unhealthy Consul cluster",
                                    "description": "Example response when Consul is not accessible",
                                    "value": {
                                        "consul_healthy": False,
                                        "leader": None,
                                        "peers_count": 0,
                                        "service_registered": False,
                                        "service_id": None,
                                        "service_name": None,
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_consul_status_endpoint() -> ConsulStatusResponse:
            """Get Consul Status Endpoint.

            Arguments:
                None

            Returns:
                ConsulStatusResponse: Consul cluster and service status information.

            Raises:
                HTTPException: If Consul is not available or status check fails.
            """

            return await self.get_consul_status()

        @self.router.get(
            path="/discover/{service_name}",
            response_model=ConsulServiceDiscoveryResponse,
            status_code=status.HTTP_200_OK,
            summary="Discover Service Instances",
            description="Discover and retrieve information about service instances registered in Consul by service name.",  # noqa: E501
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Consul is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "consul_disabled": {
                                    "summary": "Consul disabled",
                                    "description": "Example response when Consul is disabled for service discovery",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Consul service discovery is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "consul_unavailable": {
                                    "summary": "Consul unavailable",
                                    "description": "Example response when Consul service is unavailable",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Consul service is temporarily unavailable",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during service discovery",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "service_discovery_error": {
                                    "summary": "Service discovery error",
                                    "description": "Example response when service discovery encounters an internal error",  # noqa: E501
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
                    "description": "Validation error in path parameters",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "validation_error": {
                                    "summary": "Parameter validation error",
                                    "description": "Example response when service name parameter fails validation",
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
                status.HTTP_200_OK: {
                    "description": "Service discovery completed successfully",
                    "model": ConsulServiceDiscoveryResponse,
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
                                "services_found": {
                                    "summary": "Services found",
                                    "description": "Example response when service instances are found",
                                    "value": {
                                        "service_name": "initstack-fastapi-service",
                                        "instances_found": 2,
                                        "instances": [
                                            {
                                                "service_id": "initstack-fastapi-service-172.18.0.23-8000-07173d81",
                                                "service_name": "initstack-fastapi-service",
                                                "address": "172.18.0.23",
                                                "port": 8000,
                                                "tags": ["fastapi", "api", "web"],
                                                "meta": {
                                                    "debug": "true",
                                                    "description": "Professional FastAPI Server For Development.",
                                                    "environment": "development",
                                                    "version": "0.1.0",
                                                },
                                            },
                                            {
                                                "service_id": "initstack-fastapi-service-172.18.0.23-8000-5e2c97f0",
                                                "service_name": "initstack-fastapi-service",
                                                "address": "172.18.0.23",
                                                "port": 8000,
                                                "tags": ["fastapi", "api", "web"],
                                                "meta": {
                                                    "debug": "true",
                                                    "description": "Professional FastAPI Server For Development.",
                                                    "environment": "development",
                                                    "version": "0.1.0",
                                                },
                                            },
                                        ],
                                        "timestamp": "2025-12-16T12:38:58.386953+00:00",
                                    },
                                },
                                "no_services_found": {
                                    "summary": "No services found",
                                    "description": "Example response when no service instances are found",
                                    "value": {
                                        "service_name": "nonexistent-service",
                                        "instances_found": 0,
                                        "instances": [],
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def discover_service_endpoint(
            service_name: str,
            *,
            passing_only: bool = Query(
                default=True,
                description="Return only healthy service instances",
                examples=[True, False],
            ),
        ) -> ConsulServiceDiscoveryResponse:
            """Discover Service Instances Endpoint.

            Arguments:
                service_name (str): Name of the service to discover.
                passing_only (bool): Return only healthy instances (default: True).

            Returns:
                ConsulServiceDiscoveryResponse: Service discovery results.

            Raises:
                HTTPException: If Consul is not available or discovery fails.
            """

            return await self.discover_service(service_name=service_name, passing_only=passing_only)

        @self.router.get(
            path="/health/{service_name}",
            response_model=ConsulServiceHealth,
            status_code=status.HTTP_200_OK,
            summary="Get Service Health",
            description="Get detailed health information for a specific service including all instances and their health checks.",  # noqa: E501
            responses={
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Consul is not enabled or not available",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "consul_disabled": {
                                    "summary": "Consul disabled",
                                    "description": "Example response when Consul is disabled for health checks",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Consul service discovery is not enabled",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                                "consul_unavailable": {
                                    "summary": "Consul unavailable",
                                    "description": "Example response when Consul service is unavailable for health checks",  # noqa: E501
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "Consul service is temporarily unavailable",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during health check retrieval",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "health_check_error": {
                                    "summary": "Health check retrieval error",
                                    "description": "Example response when health check retrieval encounters an internal error",  # noqa: E501
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
                    "description": "Validation error in path parameters",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "validation_error": {
                                    "summary": "Parameter validation error",
                                    "description": "Example response when service name parameter fails validation",
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
                status.HTTP_200_OK: {
                    "description": "Service health information retrieved successfully",
                    "model": ConsulServiceHealth,
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
                                "healthy_service": {
                                    "summary": "Healthy service",
                                    "description": "Example response for a healthy service with passing health checks",
                                    "value": {
                                        "service_name": "initstack-fastapi-service",
                                        "instances_count": 2,
                                        "healthy_instances": 2,
                                        "instances": [
                                            {
                                                "service_id": "initstack-fastapi-service-172.18.0.23-8000-07173d81",
                                                "address": "172.18.0.23",
                                                "port": 8000,
                                                "tags": ["fastapi", "api", "web"],
                                                "meta": {
                                                    "debug": "true",
                                                    "description": "Professional FastAPI Server For Development.",
                                                    "environment": "development",
                                                    "version": "0.1.0",
                                                },
                                                "health_status": "passing",
                                                "checks": [
                                                    {
                                                        "name": "Serf Health Status",
                                                        "status": "passing",
                                                        "output": "Agent alive and reachable",
                                                    },
                                                    {
                                                        "name": "Service 'initstack-fastapi-service' check",
                                                        "status": "passing",
                                                        "output": 'HTTP GET http://172.18.0.23:8000/api/v1/health/: 200 OK Output: {"status":"healthy","timestamp":"2025-12-16T12:38:00.624004+00:00","uptime_seconds":3.08}',  # noqa: E501
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                },
                                "unhealthy_service": {
                                    "summary": "Unhealthy service",
                                    "description": "Example response for a service with failing health checks",
                                    "value": {
                                        "service_name": "database-service",
                                        "instances_count": 1,
                                        "healthy_instances": 0,
                                        "instances": [
                                            {
                                                "service_id": "database-service-172.18.0.20-5432-abc123",
                                                "address": "172.18.0.20",
                                                "port": 5432,
                                                "tags": ["database", "postgres"],
                                                "meta": {"version": "14.5"},
                                                "health_status": "critical",
                                                "checks": [
                                                    {
                                                        "name": "TCP port check",
                                                        "status": "critical",
                                                        "output": "Connection refused",
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_service_health_endpoint(service_name: str) -> ConsulServiceHealth:
            """Get Service Health Endpoint.

            Arguments:
                service_name (str): Name of the service to check health for.

            Returns:
                ConsulServiceHealth: Service health information.

            Raises:
                HTTPException: If Consul is not available or health check fails.
            """

            return await self.get_service_health(service_name=service_name)

    async def get_consul_status(self) -> ConsulStatusResponse:
        """Get Consul Cluster And Service Status.

        Arguments:
            None

        Returns:
            ConsulStatusResponse: Consul status information.

        Raises:
            HTTPException: If Consul is not available or status check fails.
        """

        try:
            self._logger.info(msg="Getting Consul status")

            if not settings.consul_enabled:
                self._logger.warning(msg="Consul is not enabled")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Consul service discovery is not enabled",
                )

            consul_adapter: ConsulAdapter = await get_consul_adapter()

            consul_healthy: bool = await consul_adapter.health_check()
            leader = None
            peers_count = 0

            if consul_healthy:
                try:
                    leader: str | None = await consul_adapter._client.status.leader()  # noqa: SLF001
                    peers: list[str] | None = await consul_adapter._client.status.peers()  # noqa: SLF001
                    peers_count: int = len(peers) if peers else 0
                except Exception as exc:
                    self._logger.warning(
                        msg=f"Failed to get Consul cluster info: {exc!s}",
                        extra={"exception_type": type(exc).__name__},
                    )

            status_response = ConsulStatusResponse(
                consul_healthy=consul_healthy,
                leader=leader,
                peers_count=peers_count,
                service_registered=consul_adapter.is_registered,
                service_id=consul_adapter.service_id if consul_adapter.is_registered else None,
                service_name=consul_adapter.service_name if consul_adapter.is_registered else None,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Consul status retrieved successfully",
                extra={
                    "consul_healthy": consul_healthy,
                    "service_registered": consul_adapter.is_registered,
                    "peers_count": peers_count,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get Consul status: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Consul status",
            ) from exc

        else:
            return status_response

    async def discover_service(self, service_name: str, *, passing_only: bool = True) -> ConsulServiceDiscoveryResponse:
        """Discover Services By Name.

        Arguments:
            service_name (str): Name of the service to discover.
            passing_only (bool): Return only healthy instances (default: True).

        Returns:
            ConsulServiceDiscoveryResponse: Service discovery results.

        Raises:
            HTTPException: If Consul is not available or discovery fails.
        """

        try:
            self._logger.info(
                msg="Discovering services",
                extra={"service_name": service_name, "passing_only": passing_only},
            )

            await self._check_consul_enabled()

            consul_adapter: ConsulAdapter = await get_consul_adapter()
            discovered_services: list[dict[str, Any]] = await consul_adapter.discover_services(
                service_name=service_name,
                passing_only=passing_only,
            )

            instances: list[ConsulServiceInstance] = [
                ConsulServiceInstance(
                    service_id=service["service_id"],
                    service_name=service["service_name"],
                    address=service["address"],
                    port=service["port"],
                    tags=service["tags"],
                    meta=service["meta"],
                )
                for service in discovered_services
            ]

            discovery_response = ConsulServiceDiscoveryResponse(
                service_name=service_name,
                instances_found=len(instances),
                instances=instances,
                timestamp=datetime.now(tz=UTC),
            )

            self._logger.info(
                msg="Service discovery completed",
                extra={
                    "service_name": service_name,
                    "instances_found": len(instances),
                    "passing_only": passing_only,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to discover services: {exc!s}",
                extra={
                    "service_name": service_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to discover services",
            ) from exc

        else:
            return discovery_response

    async def get_service_health(self, service_name: str) -> ConsulServiceHealth:
        """Get Service Health Information.

        Arguments:
            service_name (str): Name of the service to check health for.

        Returns:
            ConsulServiceHealth: Service health information.

        Raises:
            HTTPException: If Consul is not available or health check fails.
        """

        try:
            self._logger.info(
                msg="Getting service health",
                extra={"service_name": service_name},
            )

            await self._check_consul_enabled()

            consul_adapter: ConsulAdapter = await get_consul_adapter()
            health_data = await consul_adapter.get_service_health(service_name=service_name)

            health_response = ConsulServiceHealth(**health_data)

            self._logger.info(
                msg="Service health retrieved successfully",
                extra={
                    "service_name": service_name,
                    "instances_count": health_response.instances_count,
                    "healthy_instances": health_response.healthy_instances,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get service health: {exc!s}",
                extra={
                    "service_name": service_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve service health",
            ) from exc

        else:
            return health_response

    async def _check_consul_enabled(self) -> None:
        """Check If Consul Is Enabled And Available.

        Arguments:
            None

        Returns:
            None

        Raises:
            HTTPException: If Consul is not enabled.
        """

        if not settings.consul_enabled:
            self._logger.warning(msg="Consul is not enabled")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Consul service discovery is not enabled",
            )


consul_controller: ConsulController = ConsulController()


__all__: list[str] = ["ConsulController", "consul_controller"]
