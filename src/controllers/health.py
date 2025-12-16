import os
import platform
import time
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

import psutil
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from config.logger import get_logger
from config.settings import settings
from src.models import CPUInfo
from src.models import DiskInfo
from src.models import ErrorResponse
from src.models import HealthResponse
from src.models import MemoryInfo
from src.models import ProcessInfo
from src.models import SystemInfo

if TYPE_CHECKING:
    import logging


class HealthController:
    """Health Check Controller For System Monitoring.

    Inherits:
        object

    Attributes:
        _start_time (float): Application start time for uptime calculation.
        _logger (logging.Logger): Logger instance for health check operations.
        router (APIRouter): FastAPI router for health endpoints.

    Properties:
        None

    Methods:
        get_health_status: Get comprehensive system health information.
        get_health_endpoint: FastAPI endpoint for health checks.
        _get_system_info: Get system information.
        _get_cpu_info: Get CPU information.
        _get_memory_info: Get memory information.
        _get_disk_info: Get disk information.
        _get_process_info: Get current process information.
        _calculate_uptime: Calculate application uptime.
        _determine_health_status: Determine overall health status.
        _setup_routes: Setup FastAPI routes for health endpoints.
    """

    def __init__(self) -> None:
        """Initialize Health Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._start_time: float = time.time()
        self._logger: logging.Logger = get_logger(name="controller.health")
        self.router: APIRouter = APIRouter(prefix="/health", tags=["Health"])
        self._setup_routes()

    async def get_health_status(self) -> HealthResponse:
        """Get Comprehensive System Health Information.

        Arguments:
            None

        Returns:
            HealthResponse: Complete health check information.

        Raises:
            Exception: If health check fails.
        """

        try:
            self._logger.info(msg="Performing health check")

            system_info: SystemInfo = self._get_system_info()
            cpu_info: CPUInfo = self._get_cpu_info()
            memory_info: MemoryInfo = self._get_memory_info()
            disk_info: DiskInfo = self._get_disk_info()
            process_info: ProcessInfo = self._get_process_info()
            uptime: float = self._calculate_uptime()
            status: str = self._determine_health_status(
                cpu_usage=cpu_info.usage_percent,
                memory_usage=memory_info.usage_percent,
                disk_usage=disk_info.usage_percent,
            )

            additional_info: dict[str, Any] = {
                "version": settings.app_version,
                "environment": settings.environment,
                "debug_mode": settings.debug,
            }

            health_response: HealthResponse = HealthResponse(
                status=status,
                timestamp=datetime.now(tz=UTC),
                uptime_seconds=uptime,
                system=system_info,
                cpu=cpu_info,
                memory=memory_info,
                disk=disk_info,
                process=process_info,
                additional_info=additional_info,
            )

            self._logger.info(
                msg=f"Health check completed with status: {status}",
                extra={
                    "status": status,
                    "uptime_seconds": uptime,
                    "cpu_usage": cpu_info.usage_percent,
                    "memory_usage": memory_info.usage_percent,
                    "disk_usage": disk_info.usage_percent,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise

        else:
            return health_response

    def _get_system_info(self) -> SystemInfo:
        """Get System Information.

        Arguments:
            None

        Returns:
            SystemInfo: System information model.

        Raises:
            None
        """

        return SystemInfo(
            platform=platform.platform(),
            architecture=platform.machine(),
            hostname=platform.node(),
            python_version=platform.python_version(),
        )

    def _get_cpu_info(self) -> CPUInfo:
        """Get CPU Information.

        Arguments:
            None

        Returns:
            CPUInfo: CPU information model.

        Raises:
            None
        """

        cpu_count: int = psutil.cpu_count(logical=True) or 1
        cpu_usage: float = psutil.cpu_percent(interval=1)
        cpu_freq: float = psutil.cpu_freq()  # ty:ignore[possibly-missing-attribute]
        frequency: float = cpu_freq.current if cpu_freq else 0.0

        return CPUInfo(
            count=cpu_count,
            usage_percent=round(number=cpu_usage, ndigits=2),
            frequency_mhz=round(number=frequency, ndigits=2),
        )

    def _get_memory_info(self) -> MemoryInfo:
        """Get Memory Information.

        Arguments:
            None

        Returns:
            MemoryInfo: Memory information model.

        Raises:
            None
        """

        memory = psutil.virtual_memory()

        return MemoryInfo(
            total_bytes=memory.total,
            available_bytes=memory.available,
            used_bytes=memory.used,
            usage_percent=round(number=memory.percent, ndigits=2),
        )

    def _get_disk_info(self) -> DiskInfo:
        """Get Disk Information.

        Arguments:
            None

        Returns:
            DiskInfo: Disk information model.

        Raises:
            None
        """

        disk_path: str = "/" if os.name == "posix" else "C:\\"
        disk_usage = psutil.disk_usage(path=disk_path)

        return DiskInfo(
            total_bytes=disk_usage.total,
            used_bytes=disk_usage.used,
            free_bytes=disk_usage.free,
            usage_percent=round(number=(disk_usage.used / disk_usage.total) * 100, ndigits=2),
        )

    def _get_process_info(self) -> ProcessInfo:
        """Get Current Process Information.

        Arguments:
            None

        Returns:
            ProcessInfo: Process information model.

        Raises:
            None
        """

        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent: float = process.cpu_percent()

        try:
            open_files_count: int = len(process.open_files())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            open_files_count: int = 0

        return ProcessInfo(
            pid=process.pid,
            memory_usage_bytes=memory_info.rss,
            cpu_usage_percent=round(number=cpu_percent, ndigits=2),
            threads_count=process.num_threads(),
            open_files_count=open_files_count,
        )

    def _calculate_uptime(self) -> float:
        """Calculate Application Uptime.

        Arguments:
            None

        Returns:
            float: Uptime in seconds.

        Raises:
            None
        """

        return round(number=time.time() - self._start_time, ndigits=2)

    def _determine_health_status(self, cpu_usage: float, memory_usage: float, disk_usage: float) -> str:
        """Determine Overall Health Status.

        Arguments:
            cpu_usage (float): CPU usage percentage.
            memory_usage (float): Memory usage percentage.
            disk_usage (float): Disk usage percentage.

        Returns:
            str: Health status ("healthy", "degraded", or "unhealthy").

        Raises:
            None
        """

        if cpu_usage > 90 or memory_usage > 90 or disk_usage > 95:  # noqa: PLR2004
            return "unhealthy"
        if cpu_usage > 70 or memory_usage > 80 or disk_usage > 85:  # noqa: PLR2004
            return "degraded"
        return "healthy"

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For Health Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.get(
            path="/",
            response_model=HealthResponse,
            status_code=status.HTTP_200_OK,
            summary="System Health Check",
            description="Get comprehensive system health information including CPU, memory, disk usage, and process details.",  # noqa: E501
            responses={
                status.HTTP_200_OK: {
                    "description": "Health check successful",
                    "model": HealthResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "healthy_system": {
                                    "summary": "Healthy system example",
                                    "description": "Example response when all system metrics are within normal ranges",
                                    "value": {
                                        "status": "healthy",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                        "uptime_seconds": 3600.5,
                                        "system": {
                                            "platform": "Windows-10-10.0.19045-SP0",
                                            "architecture": "AMD64",
                                            "hostname": "DESKTOP-ABC123",
                                            "python_version": "3.11.5",
                                        },
                                        "cpu": {
                                            "count": 8,
                                            "usage_percent": 25.4,
                                            "frequency_mhz": 2400.0,
                                        },
                                        "memory": {
                                            "total_bytes": 17179869184,
                                            "available_bytes": 12884901888,
                                            "used_bytes": 4294967296,
                                            "usage_percent": 25.0,
                                        },
                                        "disk": {
                                            "total_bytes": 1099511627776,
                                            "used_bytes": 274877906944,
                                            "free_bytes": 824633720832,
                                            "usage_percent": 25.0,
                                        },
                                        "process": {
                                            "pid": 12345,
                                            "memory_usage_bytes": 134217728,
                                            "cpu_usage_percent": 2.5,
                                            "threads_count": 8,
                                            "open_files_count": 25,
                                        },
                                        "additional_info": {
                                            "version": "0.1.0",
                                            "environment": "development",
                                            "debug_mode": True,
                                        },
                                    },
                                },
                                "degraded_system": {
                                    "summary": "Degraded system example",
                                    "description": "Example response when system metrics indicate performance degradation",  # noqa: E501
                                    "value": {
                                        "status": "degraded",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                        "uptime_seconds": 86400.0,
                                        "system": {
                                            "platform": "Linux-5.15.0-generic",
                                            "architecture": "x86_64",
                                            "hostname": "server-01",
                                            "python_version": "3.11.5",
                                        },
                                        "cpu": {
                                            "count": 4,
                                            "usage_percent": 75.8,
                                            "frequency_mhz": 2200.0,
                                        },
                                        "memory": {
                                            "total_bytes": 8589934592,
                                            "available_bytes": 1717986918,
                                            "used_bytes": 6871947674,
                                            "usage_percent": 80.0,
                                        },
                                        "disk": {
                                            "total_bytes": 536870912000,
                                            "used_bytes": 456340275200,
                                            "free_bytes": 80530636800,
                                            "usage_percent": 85.0,
                                        },
                                        "process": {
                                            "pid": 5678,
                                            "memory_usage_bytes": 268435456,
                                            "cpu_usage_percent": 15.3,
                                            "threads_count": 12,
                                            "open_files_count": 45,
                                        },
                                        "additional_info": {
                                            "version": "0.1.0",
                                            "environment": "production",
                                            "debug_mode": False,
                                        },
                                    },
                                },
                                "unhealthy_system": {
                                    "summary": "Unhealthy system example",
                                    "description": "Example response when system metrics indicate critical resource usage",  # noqa: E501
                                    "value": {
                                        "status": "unhealthy",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                        "uptime_seconds": 604800.25,
                                        "system": {
                                            "platform": "Darwin-22.1.0",
                                            "architecture": "arm64",
                                            "hostname": "macbook-pro",
                                            "python_version": "3.12.1",
                                        },
                                        "cpu": {
                                            "count": 8,
                                            "usage_percent": 95.2,
                                            "frequency_mhz": 3200.0,
                                        },
                                        "memory": {
                                            "total_bytes": 34359738368,
                                            "available_bytes": 3435973836,
                                            "used_bytes": 30923764532,
                                            "usage_percent": 90.0,
                                        },
                                        "disk": {
                                            "total_bytes": 2199023255552,
                                            "used_bytes": 2089072193024,
                                            "free_bytes": 109951062528,
                                            "usage_percent": 95.0,
                                        },
                                        "process": {
                                            "pid": 9012,
                                            "memory_usage_bytes": 536870912,
                                            "cpu_usage_percent": 25.7,
                                            "threads_count": 16,
                                            "open_files_count": 75,
                                        },
                                        "additional_info": {
                                            "version": "0.1.0",
                                            "environment": "production",
                                            "debug_mode": False,
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Internal server error during health check",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "health_check_failure": {
                                    "summary": "Health check failure",
                                    "description": "Example response when health check encounters an internal error",
                                    "value": {
                                        "error": "Internal Server Error",
                                        "detail": "An Unexpected Error Occurred",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
                status.HTTP_503_SERVICE_UNAVAILABLE: {
                    "description": "Service temporarily unavailable",
                    "model": ErrorResponse,
                    "content": {
                        "application/json": {
                            "examples": {
                                "service_unavailable": {
                                    "summary": "Service unavailable",
                                    "description": "Example response when service is temporarily unavailable",
                                    "value": {
                                        "error": "Service Unavailable",
                                        "detail": "HTTP 503",
                                        "timestamp": "2025-01-01T12:34:56Z",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        )
        async def get_health_endpoint() -> HealthResponse:
            """Get System Health Information Endpoint.

            Arguments:
                None

            Returns:
                HealthResponse: Comprehensive system health information including CPU, memory, disk usage, and process details.

            Raises:
                HTTPException: If health check fails or service is unavailable.
            """  # noqa: E501

            try:
                self._logger.info(msg="Health check endpoint accessed")
                health_data: HealthResponse = await self.get_health_status()

                self._logger.info(
                    msg=f"Health check completed successfully with status: {health_data.status}",
                    extra={"health_status": health_data.status},
                )

            except Exception as exc:
                self._logger.exception(
                    msg=f"Health check failed: {exc!s}",
                    extra={"exception_type": type(exc).__name__},
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Health check failed",
                ) from exc

            else:
                return health_data


health_controller: HealthController = HealthController()


__all__: list[str] = ["HealthController", "health_controller"]
