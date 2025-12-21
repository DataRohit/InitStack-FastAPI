from config.adapters.consul import ConsulAdapter
from config.adapters.consul import get_consul_adapter
from config.adapters.consul import initialize_consul
from config.adapters.consul import shutdown_consul
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
    "RabbitMQAdapter",
    "RedisAdapter",
    "build_apm_config",
    "get_consul_adapter",
    "get_rabbitmq_adapter",
    "get_redis_adapter",
    "initialize_consul",
    "initialize_rabbitmq",
    "initialize_redis",
    "setup_telemetry",
    "shutdown_consul",
    "shutdown_rabbitmq",
    "shutdown_redis",
]
