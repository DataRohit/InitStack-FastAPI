from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ElasticsearchConnectionInfo(BaseModel):
    """Elasticsearch Connection Information Model.

    Inherits:
        BaseModel

    Attributes:
        hosts (list[str]): Elasticsearch server hosts.
        username (str): Elasticsearch username.
        ssl_enabled (bool): Whether SSL is enabled.
        connection_timeout (int): Connection timeout in seconds.
        request_timeout (int): Request timeout in seconds.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    hosts: list[str] = Field(
        description="Elasticsearch server hosts",
        examples=[
            ["http://localhost:9200"],
            ["http://es-node1:9200", "http://es-node2:9200"],
        ],
    )
    username: str = Field(
        description="Elasticsearch username",
        examples=["elastic", "admin"],
    )
    ssl_enabled: bool = Field(
        description="Whether SSL is enabled",
        examples=[False, True],
    )
    connection_timeout: int = Field(
        description="Connection timeout in seconds",
        examples=[10, 30, 60],
        ge=1,
        le=300,
    )
    request_timeout: int = Field(
        description="Request timeout in seconds",
        examples=[30, 60, 120],
        ge=1,
        le=600,
    )


class ElasticsearchClusterInfo(BaseModel):
    """Elasticsearch Cluster Information Model.

    Inherits:
        BaseModel

    Attributes:
        name (str | None): Cluster name.
        version (str | None): Elasticsearch version.
        status (str | None): Cluster health status.
        number_of_nodes (int | None): Number of nodes in cluster.
        active_shards (int | None): Number of active shards.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    name: str | None = Field(
        default=None,
        description="Cluster name",
        examples=["initstack-cluster", "production-cluster"],
    )
    version: str | None = Field(
        default=None,
        description="Elasticsearch version",
        examples=["9.2.0", "8.15.0"],
    )
    status: str | None = Field(
        default=None,
        description="Cluster health status",
        examples=["green", "yellow", "red"],
    )
    number_of_nodes: int | None = Field(
        default=None,
        description="Number of nodes in cluster",
        examples=[1, 3, 5],
        ge=0,
    )
    active_shards: int | None = Field(
        default=None,
        description="Number of active shards",
        examples=[0, 10, 100],
        ge=0,
    )


class ElasticsearchIndexInfo(BaseModel):
    """Elasticsearch Index Information Model.

    Inherits:
        BaseModel

    Attributes:
        name (str): Index name.
        health (str | None): Index health status.
        status (str | None): Index status.
        docs_count (int | None): Number of documents in index.
        store_size (str | None): Index storage size.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    name: str = Field(
        description="Index name",
        examples=["test_index", "users", "products"],
    )
    health: str | None = Field(
        default=None,
        description="Index health status",
        examples=["green", "yellow", "red"],
    )
    status: str | None = Field(
        default=None,
        description="Index status",
        examples=["open", "close"],
    )
    docs_count: int | None = Field(
        default=None,
        description="Number of documents in index",
        examples=[0, 100, 10000],
        ge=0,
    )
    store_size: str | None = Field(
        default=None,
        description="Index storage size",
        examples=["1kb", "10mb", "1gb"],
    )


class ElasticsearchStatusResponse(BaseModel):
    """Elasticsearch Status Response Model.

    Inherits:
        BaseModel

    Attributes:
        elasticsearch_enabled (bool): Whether Elasticsearch is enabled in configuration.
        elasticsearch_connected (bool): Whether Elasticsearch connection is established.
        connection_info (ElasticsearchConnectionInfo | None): Elasticsearch connection information.
        cluster_info (ElasticsearchClusterInfo | None): Elasticsearch cluster information.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    elasticsearch_enabled: bool = Field(
        description="Whether Elasticsearch is enabled in configuration",
        examples=[True, False],
    )
    elasticsearch_connected: bool = Field(
        description="Whether Elasticsearch connection is established",
        examples=[True, False],
    )
    connection_info: ElasticsearchConnectionInfo | None = Field(
        default=None,
        description="Elasticsearch connection information",
    )
    cluster_info: ElasticsearchClusterInfo | None = Field(
        default=None,
        description="Elasticsearch cluster information",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


class ElasticsearchTestOperation(BaseModel):
    """Elasticsearch Test Operation Model.

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
        examples=["create_index", "index_document", "search", "delete_index"],
    )
    success: bool = Field(
        description="Whether operation succeeded",
        examples=[True, False],
    )
    duration_ms: float = Field(
        description="Operation duration in milliseconds",
        examples=[1.23, 5.67, 25.89],
        ge=0.0,
    )
    result: Any | None = Field(
        default=None,
        description="Operation result",
        examples=[True, "document_id_123", 42, None],
    )
    error: str | None = Field(
        default=None,
        description="Error message if operation failed",
        examples=[None, "Elasticsearch operation failed: index not found", "Connection timeout"],
    )


class ElasticsearchTestResponse(BaseModel):
    """Elasticsearch Test Response Model.

    Inherits:
        BaseModel

    Attributes:
        elasticsearch_connected (bool): Whether Elasticsearch connection is established.
        operations_tested (int): Number of operations tested.
        operations_successful (int): Number of successful operations.
        operations_failed (int): Number of failed operations.
        total_duration_ms (float): Total test duration in milliseconds.
        operations (list[ElasticsearchTestOperation]): List of test operations.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    elasticsearch_connected: bool = Field(
        description="Whether Elasticsearch connection is established",
        examples=[True, False],
    )
    operations_tested: int = Field(
        description="Number of operations tested",
        examples=[7, 10, 15],
        ge=0,
    )
    operations_successful: int = Field(
        description="Number of successful operations",
        examples=[7, 8, 12],
        ge=0,
    )
    operations_failed: int = Field(
        description="Number of failed operations",
        examples=[0, 2, 3],
        ge=0,
    )
    total_duration_ms: float = Field(
        description="Total test duration in milliseconds",
        examples=[45.67, 78.34, 156.78],
        ge=0.0,
    )
    operations: list[ElasticsearchTestOperation] = Field(
        description="List of test operations",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = [
    "ElasticsearchClusterInfo",
    "ElasticsearchConnectionInfo",
    "ElasticsearchIndexInfo",
    "ElasticsearchStatusResponse",
    "ElasticsearchTestOperation",
    "ElasticsearchTestResponse",
]
