from src.schemas.base import ErrorResponse
from src.schemas.consul import ConsulHealthCheck
from src.schemas.consul import ConsulServiceDiscoveryResponse
from src.schemas.consul import ConsulServiceHealth
from src.schemas.consul import ConsulServiceInstance
from src.schemas.consul import ConsulServiceInstanceHealth
from src.schemas.consul import ConsulStatusResponse
from src.schemas.health import CPUInfo
from src.schemas.health import DiskInfo
from src.schemas.health import HealthResponse
from src.schemas.health import MemoryInfo
from src.schemas.health import ProcessInfo
from src.schemas.health import SystemInfo

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
