from src.controllers import telemetry_controller
from src.controllers.auth import AuthController
from src.controllers.auth import auth_controller
from src.controllers.consul import ConsulController
from src.controllers.consul import consul_controller
from src.controllers.elasticsearch import ElasticsearchController
from src.controllers.elasticsearch import elasticsearch_controller
from src.controllers.health import HealthController
from src.controllers.health import health_controller
from src.controllers.rabbitmq import RabbitMQController
from src.controllers.rabbitmq import rabbitmq_controller
from src.controllers.rate_limit import RateLimitController
from src.controllers.rate_limit import rate_limit_controller
from src.controllers.redis import RedisController
from src.controllers.redis import redis_controller
from src.controllers.websocket import ping_websocket_controller
from src.controllers.websocket import protected_ping_websocket_controller

__all__: list[str] = [
    "AuthController",
    "ConsulController",
    "ElasticsearchController",
    "HealthController",
    "RabbitMQController",
    "RateLimitController",
    "RedisController",
    "auth_controller",
    "consul_controller",
    "elasticsearch_controller",
    "health_controller",
    "ping_websocket_controller",
    "protected_ping_websocket_controller",
    "rabbitmq_controller",
    "rate_limit_controller",
    "redis_controller",
    "telemetry_controller",
]
