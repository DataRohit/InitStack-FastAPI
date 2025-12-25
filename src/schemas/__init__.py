from src.schemas.base import ErrorResponse
from src.schemas.base import ValidationErrorItem
from src.schemas.base import ValidationErrorResponse
from src.schemas.consul import ConsulHealthCheck
from src.schemas.consul import ConsulServiceDiscoveryResponse
from src.schemas.consul import ConsulServiceHealth
from src.schemas.consul import ConsulServiceInstance
from src.schemas.consul import ConsulServiceInstanceHealth
from src.schemas.consul import ConsulStatusResponse
from src.schemas.elasticsearch import ElasticsearchClusterInfo
from src.schemas.elasticsearch import ElasticsearchConnectionInfo
from src.schemas.elasticsearch import ElasticsearchIndexInfo
from src.schemas.elasticsearch import ElasticsearchStatusResponse
from src.schemas.elasticsearch import ElasticsearchTestOperation
from src.schemas.elasticsearch import ElasticsearchTestResponse
from src.schemas.health import CPUInfo
from src.schemas.health import DiskInfo
from src.schemas.health import HealthResponse
from src.schemas.health import MemoryInfo
from src.schemas.health import ProcessInfo
from src.schemas.health import SystemInfo
from src.schemas.rabbitmq import RabbitMQChannelInfo
from src.schemas.rabbitmq import RabbitMQConnectionInfo
from src.schemas.rabbitmq import RabbitMQQueueInfo
from src.schemas.rabbitmq import RabbitMQStatusResponse
from src.schemas.rabbitmq import RabbitMQTestOperation
from src.schemas.rabbitmq import RabbitMQTestResponse

__all__: list[str] = [
    "CPUInfo",
    "ConsulHealthCheck",
    "ConsulServiceDiscoveryResponse",
    "ConsulServiceHealth",
    "ConsulServiceInstance",
    "ConsulServiceInstanceHealth",
    "ConsulStatusResponse",
    "DiskInfo",
    "ElasticsearchClusterInfo",
    "ElasticsearchConnectionInfo",
    "ElasticsearchIndexInfo",
    "ElasticsearchStatusResponse",
    "ElasticsearchTestOperation",
    "ElasticsearchTestResponse",
    "ErrorResponse",
    "HealthResponse",
    "MemoryInfo",
    "ProcessInfo",
    "RabbitMQChannelInfo",
    "RabbitMQConnectionInfo",
    "RabbitMQQueueInfo",
    "RabbitMQStatusResponse",
    "RabbitMQTestOperation",
    "RabbitMQTestResponse",
    "SystemInfo",
    "ValidationErrorItem",
    "ValidationErrorResponse",
]
