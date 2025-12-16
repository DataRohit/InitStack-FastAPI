from src.controllers.consul import ConsulController
from src.controllers.consul import consul_controller
from src.controllers.health import HealthController
from src.controllers.health import health_controller

__all__: list[str] = ["ConsulController", "HealthController", "consul_controller", "health_controller"]
