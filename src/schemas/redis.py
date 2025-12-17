from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RedisConnectionInfo(BaseModel):
    """Redis Connection Information Model.

    Inherits:
        BaseModel

    Attributes:
        host (str): Redis server host.
        port (int): Redis server port.
        database (int): Redis database number.
        ssl_enabled (bool): Whether SSL is enabled.
        max_connections (int): Maximum connections in pool.
        connection_timeout (int): Connection timeout in seconds.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    host: str = Field(
        description="Redis server host",
        examples=["initstack-redis-service", "redis.example.com", "localhost"],
    )
    port: int = Field(
        description="Redis server port",
        examples=[6379, 6380, 26379],
        ge=1,
        le=65535,
    )
    database: int = Field(
        description="Redis database number",
        examples=[0, 1, 15],
        ge=0,
        le=15,
    )
    ssl_enabled: bool = Field(
        description="Whether SSL is enabled",
        examples=[False, True],
    )
    max_connections: int = Field(
        description="Maximum connections in pool",
        examples=[10, 50, 100],
        ge=1,
        le=1000,
    )
    connection_timeout: int = Field(
        description="Connection timeout in seconds",
        examples=[5, 10, 30],
        ge=1,
        le=300,
    )


class RedisPoolStats(BaseModel):
    """Redis Connection Pool Statistics Model.

    Inherits:
        BaseModel

    Attributes:
        status (str): Pool status.
        max_connections (int | str): Maximum connections allowed.
        available_connections (int | None): Available connections count.
        in_use_connections (int | None): In-use connections count.
        created_connections (int | None): Created connections count.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    status: str = Field(
        description="Pool status",
        examples=["initialized", "not_initialized", "error_getting_stats"],
    )
    max_connections: int | str = Field(
        description="Maximum connections allowed",
        examples=[50, 100, "unknown"],
    )
    available_connections: int | None = Field(
        default=None,
        description="Available connections count",
        examples=[48, 95, None],
        ge=0,
    )
    in_use_connections: int | None = Field(
        default=None,
        description="In-use connections count",
        examples=[2, 5, None],
        ge=0,
    )
    created_connections: int | None = Field(
        default=None,
        description="Created connections count",
        examples=[5, 10, None],
        ge=0,
    )


class RedisServerInfo(BaseModel):
    """Redis Server Information Model.

    Inherits:
        BaseModel

    Attributes:
        redis_version (str | None): Redis server version.
        redis_mode (str | None): Redis server mode.
        connected_clients (int | None): Number of connected clients.
        used_memory_human (str | None): Used memory in human readable format.
        total_commands_processed (int | None): Total commands processed.
        keyspace_hits (int | None): Keyspace hits count.
        keyspace_misses (int | None): Keyspace misses count.
        uptime_in_seconds (int | None): Server uptime in seconds.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    redis_version: str | None = Field(
        default=None,
        description="Redis server version",
        examples=["8.4.0", "7.2.4", "6.2.14"],
    )
    redis_mode: str | None = Field(
        default=None,
        description="Redis server mode",
        examples=["standalone", "cluster", "sentinel"],
    )
    connected_clients: int | None = Field(
        default=None,
        description="Number of connected clients",
        examples=[3, 15, 50],
        ge=0,
    )
    used_memory_human: str | None = Field(
        default=None,
        description="Used memory in human readable format",
        examples=["2.45M", "128.5M", "1.2G"],
    )
    total_commands_processed: int | None = Field(
        default=None,
        description="Total commands processed",
        examples=[1247, 50000, 1000000],
        ge=0,
    )
    keyspace_hits: int | None = Field(
        default=None,
        description="Keyspace hits count",
        examples=[89, 4500, 900000],
        ge=0,
    )
    keyspace_misses: int | None = Field(
        default=None,
        description="Keyspace misses count",
        examples=[12, 500, 100000],
        ge=0,
    )
    uptime_in_seconds: int | None = Field(
        default=None,
        description="Server uptime in seconds",
        examples=[3600, 86400, 604800],
        ge=0,
    )


class RedisStatusResponse(BaseModel):
    """Redis Status Response Model.

    Inherits:
        BaseModel

    Attributes:
        redis_enabled (bool): Whether Redis is enabled in configuration.
        redis_connected (bool): Whether Redis connection is established.
        connection_info (RedisConnectionInfo | None): Redis connection information.
        pool_stats (RedisPoolStats | None): Connection pool statistics.
        server_info (RedisServerInfo | None): Redis server information.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    redis_enabled: bool = Field(
        description="Whether Redis is enabled in configuration",
        examples=[True, False],
    )
    redis_connected: bool = Field(
        description="Whether Redis connection is established",
        examples=[True, False],
    )
    connection_info: RedisConnectionInfo | None = Field(
        default=None,
        description="Redis connection information",
    )
    pool_stats: RedisPoolStats | None = Field(
        default=None,
        description="Connection pool statistics",
    )
    server_info: RedisServerInfo | None = Field(
        default=None,
        description="Redis server information",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


class RedisTestOperation(BaseModel):
    """Redis Test Operation Model.

    Inherits:
        BaseModel

    Attributes:
        operation (str): Operation name.
        success (bool): Whether operation succeeded.
        duration_ms (float): Operation duration in milliseconds.
        result (Any | None): Operation result.
        error (str | None): Error message if operation failed.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    operation: str = Field(
        description="Operation name",
        examples=["ping", "set_key", "get_key", "hset_hash", "incr_counter"],
    )
    success: bool = Field(
        description="Whether operation succeeded",
        examples=[True, False],
    )
    duration_ms: float = Field(
        description="Operation duration in milliseconds",
        examples=[1.23, 2.45, 15.67],
        ge=0.0,
    )
    result: Any | None = Field(
        default=None,
        description="Operation result",
        examples=[True, "test_value", 42, None],
    )
    error: str | None = Field(
        default=None,
        description="Error message if operation failed",
        examples=[None, "Redis operation failed: connection timeout", "Invalid command syntax"],
    )


class RedisTestResponse(BaseModel):
    """Redis Test Response Model.

    Inherits:
        BaseModel

    Attributes:
        redis_connected (bool): Whether Redis connection is established.
        operations_tested (int): Number of operations tested.
        operations_successful (int): Number of successful operations.
        operations_failed (int): Number of failed operations.
        total_duration_ms (float): Total test duration in milliseconds.
        operations (list[RedisTestOperation]): List of test operations.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    redis_connected: bool = Field(
        description="Whether Redis connection is established",
        examples=[True, False],
    )
    operations_tested: int = Field(
        description="Number of operations tested",
        examples=[12, 15, 20],
        ge=0,
    )
    operations_successful: int = Field(
        description="Number of successful operations",
        examples=[12, 10, 18],
        ge=0,
    )
    operations_failed: int = Field(
        description="Number of failed operations",
        examples=[0, 2, 5],
        ge=0,
    )
    total_duration_ms: float = Field(
        description="Total test duration in milliseconds",
        examples=[45.67, 52.34, 123.45],
        ge=0.0,
    )
    operations: list[RedisTestOperation] = Field(
        description="List of test operations",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = [
    "RedisConnectionInfo",
    "RedisPoolStats",
    "RedisServerInfo",
    "RedisStatusResponse",
    "RedisTestOperation",
    "RedisTestResponse",
]
