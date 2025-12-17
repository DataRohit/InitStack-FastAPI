from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SystemInfo(BaseModel):
    """System Information Model.

    Inherits:
        BaseModel

    Attributes:
        platform (str): Operating system platform.
        architecture (str): System architecture.
        hostname (str): System hostname.
        python_version (str): Python version.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    platform: str = Field(
        default=...,
        description="Operating system platform information.",
        examples=["Windows-10-10.0.19045-SP0", "Linux-5.15.0-generic", "Darwin-22.1.0"],
    )
    architecture: str = Field(
        default=...,
        description="System architecture.",
        examples=["AMD64", "x86_64", "arm64"],
    )
    hostname: str = Field(
        default=...,
        description="System hostname.",
        examples=["DESKTOP-ABC123", "server-01", "localhost"],
    )
    python_version: str = Field(
        default=...,
        description="Python interpreter version.",
        examples=["3.11.5", "3.10.12", "3.12.1"],
    )


class CPUInfo(BaseModel):
    """CPU Information Model.

    Inherits:
        BaseModel

    Attributes:
        count (int): Number of CPU cores.
        usage_percent (float): Current CPU usage percentage.
        frequency_mhz (float): Current CPU frequency in MHz.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    count: int = Field(
        default=...,
        description="Number of CPU cores available.",
        examples=[4, 8, 16],
        ge=1,
    )
    usage_percent: float = Field(
        default=...,
        description="Current CPU usage percentage.",
        examples=[15.2, 45.8, 78.9],
        ge=0.0,
        le=100.0,
    )
    frequency_mhz: float = Field(
        default=...,
        description="Current CPU frequency in MHz.",
        examples=[1800.0, 2400.0, 3200.0],
        ge=0.0,
    )


class MemoryInfo(BaseModel):
    """Memory Information Model.

    Inherits:
        BaseModel

    Attributes:
        total_bytes (int): Total system memory in bytes.
        available_bytes (int): Available memory in bytes.
        used_bytes (int): Used memory in bytes.
        usage_percent (float): Memory usage percentage.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    total_bytes: int = Field(
        default=...,
        description="Total system memory in bytes.",
        examples=[8589934592, 17179869184, 34359738368],
        ge=0,
    )
    available_bytes: int = Field(
        default=...,
        description="Available memory in bytes.",
        examples=[4294967296, 8589934592, 17179869184],
        ge=0,
    )
    used_bytes: int = Field(
        default=...,
        description="Used memory in bytes.",
        examples=[4294967296, 8589934592, 17179869184],
        ge=0,
    )
    usage_percent: float = Field(
        default=...,
        description="Memory usage percentage.",
        examples=[25.5, 50.0, 75.8],
        ge=0.0,
        le=100.0,
    )


class DiskInfo(BaseModel):
    """Disk Information Model.

    Inherits:
        BaseModel

    Attributes:
        total_bytes (int): Total disk space in bytes.
        used_bytes (int): Used disk space in bytes.
        free_bytes (int): Free disk space in bytes.
        usage_percent (float): Disk usage percentage.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    total_bytes: int = Field(
        default=...,
        description="Total disk space in bytes.",
        examples=[536870912000, 1099511627776, 2199023255552],
        ge=0,
    )
    used_bytes: int = Field(
        default=...,
        description="Used disk space in bytes.",
        examples=[268435456000, 549755813888, 1099511627776],
        ge=0,
    )
    free_bytes: int = Field(
        default=...,
        description="Free disk space in bytes.",
        examples=[268435456000, 549755813888, 1099511627776],
        ge=0,
    )
    usage_percent: float = Field(
        default=...,
        description="Disk usage percentage.",
        examples=[25.0, 50.0, 85.7],
        ge=0.0,
        le=100.0,
    )


class ProcessInfo(BaseModel):
    """Process Information Model.

    Inherits:
        BaseModel

    Attributes:
        pid (int): Process ID.
        memory_usage_bytes (int): Process memory usage in bytes.
        cpu_usage_percent (float): Process CPU usage percentage.
        threads_count (int): Number of threads.
        open_files_count (int): Number of open file descriptors.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    pid: int = Field(
        default=...,
        description="Process ID.",
        examples=[1234, 5678, 9012],
        ge=1,
    )
    memory_usage_bytes: int = Field(
        default=...,
        description="Process memory usage in bytes.",
        examples=[67108864, 134217728, 268435456],
        ge=0,
    )
    cpu_usage_percent: float = Field(
        default=...,
        description="Process CPU usage percentage.",
        examples=[1.2, 5.8, 15.3],
        ge=0.0,
    )
    threads_count: int = Field(
        default=...,
        description="Number of threads in the process.",
        examples=[4, 8, 16],
        ge=1,
    )
    open_files_count: int = Field(
        default=...,
        description="Number of open file descriptors.",
        examples=[10, 25, 50],
        ge=0,
    )


class HealthResponse(BaseModel):
    """Health Check Response Model.

    Inherits:
        BaseModel

    Attributes:
        status (str): Health status indicator.
        timestamp (datetime): Health check timestamp.
        uptime_seconds (float): Application uptime in seconds.
        system (SystemInfo): System information.
        cpu (CPUInfo): CPU information.
        memory (MemoryInfo): Memory information.
        disk (DiskInfo): Disk information.
        process (ProcessInfo): Process information.
        additional_info (dict[str, Any]): Additional health information.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    status: str = Field(
        default=...,
        description="Health status indicator.",
        examples=["healthy", "degraded", "unhealthy"],
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp when the health check was performed.",
        examples=["2025-01-01T12:34:56Z"],
    )
    uptime_seconds: float = Field(
        default=...,
        description="Application uptime in seconds.",
        examples=[3600.5, 86400.0, 604800.25],
        ge=0.0,
    )
    system: SystemInfo = Field(
        default=...,
        description="System information.",
    )
    cpu: CPUInfo = Field(
        default=...,
        description="CPU information.",
    )
    memory: MemoryInfo = Field(
        default=...,
        description="Memory information.",
    )
    disk: DiskInfo = Field(
        default=...,
        description="Disk information.",
    )
    process: ProcessInfo = Field(
        default=...,
        description="Process information.",
    )
    additional_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional health information.",
        examples=[
            {"version": "0.1.0", "environment": "development"},
            {"database_status": "connected", "cache_status": "available"},
        ],
    )


__all__: list[str] = [
    "CPUInfo",
    "DiskInfo",
    "HealthResponse",
    "MemoryInfo",
    "ProcessInfo",
    "SystemInfo",
]
