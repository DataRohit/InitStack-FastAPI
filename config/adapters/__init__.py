from config.adapters.consul import ConsulAdapter
from config.adapters.consul import get_consul_adapter
from config.adapters.consul import initialize_consul
from config.adapters.consul import shutdown_consul
from config.adapters.elasticsearch import ElasticsearchAdapter
from config.adapters.elasticsearch import get_elasticsearch_adapter
from config.adapters.elasticsearch import initialize_elasticsearch
from config.adapters.elasticsearch import shutdown_elasticsearch
from config.adapters.email import EmailAdapter
from config.adapters.email import get_email_adapter
from config.adapters.email import initialize_email
from config.adapters.email import shutdown_email
from config.adapters.minio import MinIOAdapter
from config.adapters.minio import get_minio_adapter
from config.adapters.minio import initialize_minio
from config.adapters.minio import shutdown_minio
from config.adapters.rabbitmq import RabbitMQAdapter
from config.adapters.rabbitmq import get_rabbitmq_adapter
from config.adapters.rabbitmq import initialize_rabbitmq
from config.adapters.rabbitmq import shutdown_rabbitmq
from config.adapters.redis import RedisAdapter
from config.adapters.redis import get_redis_adapter
from config.adapters.redis import initialize_redis
from config.adapters.redis import shutdown_redis
from config.adapters.telemetry import build_apm_config
from config.adapters.telemetry import setup_telemetry

__all__: list[str] = [
    "ConsulAdapter",
    "ElasticsearchAdapter",
    "EmailAdapter",
    "MinIOAdapter",
    "RabbitMQAdapter",
    "RedisAdapter",
    "build_apm_config",
    "get_consul_adapter",
    "get_elasticsearch_adapter",
    "get_email_adapter",
    "get_minio_adapter",
    "get_rabbitmq_adapter",
    "get_redis_adapter",
    "initialize_consul",
    "initialize_elasticsearch",
    "initialize_email",
    "initialize_minio",
    "initialize_rabbitmq",
    "initialize_redis",
    "setup_telemetry",
    "shutdown_consul",
    "shutdown_elasticsearch",
    "shutdown_email",
    "shutdown_minio",
    "shutdown_rabbitmq",
    "shutdown_redis",
]
