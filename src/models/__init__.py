from src.models.base import ErrorResponse
from src.models.consul import ConsulHealthCheck
from src.models.consul import ConsulServiceDiscoveryResponse
from src.models.consul import ConsulServiceHealth
from src.models.consul import ConsulServiceInstance
from src.models.consul import ConsulServiceInstanceHealth
from src.models.consul import ConsulStatusResponse
from src.models.health import CPUInfo
from src.models.health import DiskInfo
from src.models.health import HealthResponse
from src.models.health import MemoryInfo
from src.models.health import ProcessInfo
from src.models.health import SystemInfo

__all__: list[str] = [
    "CPUInfo",
    "ConsulHealthCheck",
    "ConsulServiceDiscoveryResponse",
    "ConsulServiceHealth",
    "ConsulServiceInstance",
    "ConsulServiceInstanceHealth",
    "ConsulStatusResponse",
    "DiskInfo",
    "ErrorResponse",
    "HealthResponse",
    "MemoryInfo",
    "ProcessInfo",
    "SystemInfo",
]
