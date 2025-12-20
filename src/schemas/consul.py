from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ConsulServiceInstance(BaseModel):
    """Consul Service Instance Model.

    Inherits:
        BaseModel

    Attributes:
        service_id (str): Unique service identifier.
        service_name (str): Service name.
        address (str): Service IP address.
        port (int): Service port number.
        tags (list[str]): Service tags.
        meta (dict[str, Any]): Service metadata.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    service_id: str = Field(
        default=...,
        description="Unique service identifier in Consul.",
        examples=["initstack-fastapi-service-172.18.0.23-8080-07173d81"],
    )
    service_name: str = Field(
        default=...,
        description="Service name registered in Consul.",
        examples=["initstack-fastapi-service", "database-service", "cache-service"],
    )
    address: str = Field(
        default=...,
        description="Service IP address or hostname.",
        examples=["172.18.0.23", "192.168.1.100", "service.example.com"],
    )
    port: int = Field(
        default=...,
        description="Service port number.",
        examples=[8080, 5432, 6379],
        ge=1,
        le=65535,
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Service tags for categorization and filtering.",
        examples=[["fastapi", "api", "web"], ["database", "postgres"], ["cache", "redis"]],
    )
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Service metadata with additional information.",
        examples=[
            {
                "debug": "true",
                "description": "Professional FastAPI Server For Development.",
                "environment": "development",
                "version": "0.1.0",
            },
            {"database_version": "14.5", "max_connections": "100"},
        ],
    )


class ConsulHealthCheck(BaseModel):
    """Consul Health Check Model.

    Inherits:
        BaseModel

    Attributes:
        name (str): Health check name.
        status (str): Health check status.
        output (str): Health check output message.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    name: str = Field(
        default=...,
        description="Health check name or identifier.",
        examples=["Service health check", "HTTP endpoint check", "TCP port check"],
    )
    status: str = Field(
        default=...,
        description="Health check status.",
        examples=["passing", "warning", "critical"],
    )
    output: str = Field(
        default="",
        description="Health check output or error message.",
        examples=[
            "Agent alive and reachable",
            'HTTP GET http://172.18.0.23:8080/api/v1/health/: 200 OK Output: {"status":"healthy","timestamp":"2025-12-16T12:38:00.624004+00:00","uptime_seconds":3.08}',  # noqa: E501
            "Connection refused",
        ],
    )


class ConsulServiceHealth(BaseModel):
    """Consul Service Health Model.

    Inherits:
        BaseModel

    Attributes:
        service_name (str): Service name.
        instances_count (int): Total number of service instances.
        healthy_instances (int): Number of healthy service instances.
        instances (list[ConsulServiceInstanceHealth]): List of service instances with health info.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    service_name: str = Field(
        default=...,
        description="Service name being checked.",
        examples=["initstack-fastapi-service", "database-service", "cache-service"],
    )
    instances_count: int = Field(
        default=...,
        description="Total number of service instances registered.",
        examples=[1, 2, 5],
        ge=0,
    )
    healthy_instances: int = Field(
        default=...,
        description="Number of healthy service instances.",
        examples=[1, 2, 3],
        ge=0,
    )
    instances: list[ConsulServiceInstanceHealth] = Field(
        default_factory=list,
        description="List of service instances with health information.",
    )


class ConsulServiceInstanceHealth(BaseModel):
    """Consul Service Instance Health Model.

    Inherits:
        BaseModel

    Attributes:
        service_id (str): Unique service identifier.
        address (str): Service IP address.
        port (int): Service port number.
        tags (list[str]): Service tags.
        meta (dict[str, Any]): Service metadata.
        health_status (str): Overall health status.
        checks (list[ConsulHealthCheck]): List of health checks.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    service_id: str = Field(
        default=...,
        description="Unique service identifier.",
        examples=["initstack-fastapi-service-172.18.0.23-8080-07173d81"],
    )
    address: str = Field(
        default=...,
        description="Service IP address or hostname.",
        examples=["172.18.0.23", "192.168.1.100"],
    )
    port: int = Field(
        default=...,
        description="Service port number.",
        examples=[8080, 5432, 6379],
        ge=1,
        le=65535,
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Service tags.",
        examples=[["fastapi", "api", "web"], ["database", "postgres"]],
    )
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Service metadata.",
        examples=[
            {
                "debug": "true",
                "description": "Professional FastAPI Server For Development.",
                "environment": "development",
                "version": "0.1.0",
            },
        ],
    )
    health_status: str = Field(
        default=...,
        description="Overall health status of the service instance.",
        examples=["passing", "warning", "critical"],
    )
    checks: list[ConsulHealthCheck] = Field(
        default_factory=list,
        description="List of health checks for this service instance.",
    )


class ConsulStatusResponse(BaseModel):
    """Consul Status Response Model.

    Inherits:
        BaseModel

    Attributes:
        consul_healthy (bool): Whether Consul cluster is healthy.
        leader (str): Current Consul leader.
        peers_count (int): Number of Consul peers.
        service_registered (bool): Whether current service is registered.
        service_id (str): Current service ID.
        service_name (str): Current service name.
        timestamp (datetime): Status check timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    consul_healthy: bool = Field(
        default=...,
        description="Whether Consul cluster is healthy and accessible.",
        examples=[True, False],
    )
    leader: str | None = Field(
        default=None,
        description="Current Consul cluster leader address.",
        examples=["172.18.0.10:8300", "consul-server-1:8300"],
    )
    peers_count: int = Field(
        default=...,
        description="Number of Consul cluster peers.",
        examples=[1, 3, 5],
        ge=0,
    )
    service_registered: bool = Field(
        default=...,
        description="Whether the current service is registered with Consul.",
        examples=[True, False],
    )
    service_id: str | None = Field(
        default=None,
        description="Current service ID if registered.",
        examples=["initstack-fastapi-service-172.18.0.19-8080-402f4c44"],
    )
    service_name: str | None = Field(
        default=None,
        description="Current service name if registered.",
        examples=["initstack-fastapi-service"],
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp when the status was checked.",
        examples=["2025-01-01T12:34:56Z"],
    )


class ConsulServiceDiscoveryResponse(BaseModel):
    """Consul Service Discovery Response Model.

    Inherits:
        BaseModel

    Attributes:
        service_name (str): Service name that was searched.
        instances_found (int): Number of service instances found.
        instances (list[ConsulServiceInstance]): List of discovered service instances.
        timestamp (datetime): Discovery timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    service_name: str = Field(
        default=...,
        description="Service name that was searched for.",
        examples=["initstack-fastapi-service", "database-service", "cache-service"],
    )
    instances_found: int = Field(
        default=...,
        description="Number of service instances found.",
        examples=[0, 1, 2],
        ge=0,
    )
    instances: list[ConsulServiceInstance] = Field(
        default_factory=list,
        description="List of discovered service instances.",
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp when the discovery was performed.",
        examples=["2025-12-16T12:38:58.386953+00:00"],
    )


__all__: list[str] = [
    "ConsulHealthCheck",
    "ConsulServiceDiscoveryResponse",
    "ConsulServiceHealth",
    "ConsulServiceInstance",
    "ConsulServiceInstanceHealth",
    "ConsulStatusResponse",
]
