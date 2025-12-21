from src.controllers.consul import ConsulController
from src.controllers.consul import consul_controller
from src.controllers.health import HealthController
from src.controllers.health import health_controller
from src.controllers.rabbitmq import RabbitMQController
from src.controllers.rabbitmq import rabbitmq_controller
from src.controllers.rate_limit import RateLimitController
from src.controllers.rate_limit import rate_limit_controller
from src.controllers.redis import RedisController
from src.controllers.redis import redis_controller

__all__: list[str] = [
    "ConsulController",
    "HealthController",
    "RabbitMQController",
    "RateLimitController",
    "RedisController",
    "consul_controller",
    "health_controller",
    "rabbitmq_controller",
    "rate_limit_controller",
    "redis_controller",
]
