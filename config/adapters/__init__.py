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
from config.adapters.otel_metrics import get_meter
from config.adapters.otel_metrics import get_prometheus_metrics
from config.adapters.otel_metrics import setup_auto_instrumentation
from config.adapters.otel_metrics import setup_otel_metrics
from config.adapters.otel_metrics import setup_resource
from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from config.adapters.postgresql import initialize_postgresql
from config.adapters.postgresql import shutdown_postgresql
from config.adapters.rabbitmq import RabbitMQAdapter
from config.adapters.rabbitmq import get_rabbitmq_adapter
from config.adapters.rabbitmq import initialize_rabbitmq
from config.adapters.rabbitmq import shutdown_rabbitmq
from config.adapters.redis import RedisAdapter
from config.adapters.redis import TokenCacheRedisAdapter
from config.adapters.redis import get_redis_adapter
from config.adapters.redis import get_token_cache_redis_adapter
from config.adapters.redis import initialize_redis
from config.adapters.redis import shutdown_redis
from config.adapters.telemetry import build_apm_config
from config.adapters.telemetry import setup_telemetry

__all__: list[str] = [
    "ConsulAdapter",
    "ElasticsearchAdapter",
    "EmailAdapter",
    "MinIOAdapter",
    "PostgreSQLAdapter",
    "RabbitMQAdapter",
    "RedisAdapter",
    "TokenCacheRedisAdapter",
    "build_apm_config",
    "get_consul_adapter",
    "get_elasticsearch_adapter",
    "get_email_adapter",
    "get_meter",
    "get_minio_adapter",
    "get_postgresql_adapter",
    "get_prometheus_metrics",
    "get_rabbitmq_adapter",
    "get_redis_adapter",
    "get_token_cache_redis_adapter",
    "initialize_consul",
    "initialize_elasticsearch",
    "initialize_email",
    "initialize_minio",
    "initialize_postgresql",
    "initialize_rabbitmq",
    "initialize_redis",
    "setup_auto_instrumentation",
    "setup_otel_metrics",
    "setup_resource",
    "setup_telemetry",
    "shutdown_consul",
    "shutdown_elasticsearch",
    "shutdown_email",
    "shutdown_minio",
    "shutdown_postgresql",
    "shutdown_rabbitmq",
    "shutdown_redis",
]
