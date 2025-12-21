from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RabbitMQConnectionInfo(BaseModel):
    """RabbitMQ Connection Information Model.

    Inherits:
        BaseModel

    Attributes:
        host (str): RabbitMQ server host.
        port (int): RabbitMQ server port.
        vhost (str): RabbitMQ virtual host.
        ssl_enabled (bool): Whether SSL is enabled.
        connection_name (str): Connection name.
        connection_timeout (int): Connection timeout in seconds.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    host: str = Field(
        description="RabbitMQ server host",
        examples=["initstack-rabbitmq-service", "rabbitmq.example.com", "localhost"],
    )
    port: int = Field(
        description="RabbitMQ server port",
        examples=[5672, 5671, 15672],
        ge=1,
        le=65535,
    )
    vhost: str = Field(
        description="RabbitMQ virtual host",
        examples=["/", "/production", "/staging"],
    )
    ssl_enabled: bool = Field(
        description="Whether SSL is enabled",
        examples=[False, True],
    )
    connection_name: str = Field(
        description="Connection name",
        examples=["initstack-fastapi-service", "api-service", "worker-service"],
    )
    connection_timeout: int = Field(
        description="Connection timeout in seconds",
        examples=[10, 30, 60],
        ge=1,
        le=300,
    )


class RabbitMQChannelInfo(BaseModel):
    """RabbitMQ Channel Information Model.

    Inherits:
        BaseModel

    Attributes:
        channel_number (int | None): Channel number.
        is_closed (bool | None): Whether channel is closed.
        prefetch_count (int): Prefetch count for consumers.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    channel_number: int | None = Field(
        default=None,
        description="Channel number",
        examples=[1, 2, 10],
        ge=0,
    )
    is_closed: bool | None = Field(
        default=None,
        description="Whether channel is closed",
        examples=[False, True],
    )
    prefetch_count: int = Field(
        description="Prefetch count for consumers",
        examples=[10, 20, 50],
        ge=0,
    )


class RabbitMQQueueInfo(BaseModel):
    """RabbitMQ Queue Information Model.

    Inherits:
        BaseModel

    Attributes:
        name (str): Queue name.
        durable (bool): Whether queue is durable.
        exclusive (bool): Whether queue is exclusive.
        auto_delete (bool): Whether queue auto-deletes.
        message_count (int | None): Number of messages in queue.
        consumer_count (int | None): Number of consumers.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    name: str = Field(
        description="Queue name",
        examples=["test_queue", "task_queue", "notifications"],
    )
    durable: bool = Field(
        description="Whether queue is durable",
        examples=[True, False],
    )
    exclusive: bool = Field(
        description="Whether queue is exclusive",
        examples=[False, True],
    )
    auto_delete: bool = Field(
        description="Whether queue auto-deletes",
        examples=[False, True],
    )
    message_count: int | None = Field(
        default=None,
        description="Number of messages in queue",
        examples=[0, 10, 100],
        ge=0,
    )
    consumer_count: int | None = Field(
        default=None,
        description="Number of consumers",
        examples=[0, 1, 5],
        ge=0,
    )


class RabbitMQStatusResponse(BaseModel):
    """RabbitMQ Status Response Model.

    Inherits:
        BaseModel

    Attributes:
        rabbitmq_enabled (bool): Whether RabbitMQ is enabled in configuration.
        rabbitmq_connected (bool): Whether RabbitMQ connection is established.
        connection_info (RabbitMQConnectionInfo | None): RabbitMQ connection information.
        channel_info (RabbitMQChannelInfo | None): RabbitMQ channel information.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    rabbitmq_enabled: bool = Field(
        description="Whether RabbitMQ is enabled in configuration",
        examples=[True, False],
    )
    rabbitmq_connected: bool = Field(
        description="Whether RabbitMQ connection is established",
        examples=[True, False],
    )
    connection_info: RabbitMQConnectionInfo | None = Field(
        default=None,
        description="RabbitMQ connection information",
    )
    channel_info: RabbitMQChannelInfo | None = Field(
        default=None,
        description="RabbitMQ channel information",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


class RabbitMQTestOperation(BaseModel):
    """RabbitMQ Test Operation Model.

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
        examples=["declare_exchange", "declare_queue", "publish_message", "purge_queue"],
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
        examples=[None, "RabbitMQ operation failed: connection timeout", "Invalid queue name"],
    )


class RabbitMQTestResponse(BaseModel):
    """RabbitMQ Test Response Model.

    Inherits:
        BaseModel

    Attributes:
        rabbitmq_connected (bool): Whether RabbitMQ connection is established.
        operations_tested (int): Number of operations tested.
        operations_successful (int): Number of successful operations.
        operations_failed (int): Number of failed operations.
        total_duration_ms (float): Total test duration in milliseconds.
        operations (list[RabbitMQTestOperation]): List of test operations.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    rabbitmq_connected: bool = Field(
        description="Whether RabbitMQ connection is established",
        examples=[True, False],
    )
    operations_tested: int = Field(
        description="Number of operations tested",
        examples=[8, 10, 15],
        ge=0,
    )
    operations_successful: int = Field(
        description="Number of successful operations",
        examples=[8, 7, 12],
        ge=0,
    )
    operations_failed: int = Field(
        description="Number of failed operations",
        examples=[0, 1, 3],
        ge=0,
    )
    total_duration_ms: float = Field(
        description="Total test duration in milliseconds",
        examples=[45.67, 52.34, 123.45],
        ge=0.0,
    )
    operations: list[RabbitMQTestOperation] = Field(
        description="List of test operations",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = [
    "RabbitMQChannelInfo",
    "RabbitMQConnectionInfo",
    "RabbitMQQueueInfo",
    "RabbitMQStatusResponse",
    "RabbitMQTestOperation",
    "RabbitMQTestResponse",
]
