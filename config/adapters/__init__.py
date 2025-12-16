from config.adapters.consul import ConsulAdapter
from config.adapters.consul import get_consul_adapter
from config.adapters.consul import initialize_consul
from config.adapters.consul import shutdown_consul

__all__: list[str] = [
    "ConsulAdapter",
    "get_consul_adapter",
    "initialize_consul",
    "shutdown_consul",
]
