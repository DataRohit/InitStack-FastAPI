# Standard Library Imports
import datetime
import socket

# Third-Party Imports
import psutil
from pydantic import BaseModel, Field

# Local Imports
from config.settings import settings


# System Memory Information Model
class SystemMemory(BaseModel):
    """
    System Memory Information Model

    This Model Defines the Structure of the System Memory Information.

    Attributes:
        total (int): Total Physical Memory in Bytes
        available (int): Available Memory in Bytes
        percent (float): Percentage of Memory in Use
        used (int): Used Memory in Bytes
        free (int): Free Memory in Bytes
    """

    # Model Fields
    total: int = Field(
        ...,
        example=17179869184,  # 16GB in bytes
        description="Total Physical Memory in Bytes",
    )
    available: int = Field(
        ...,
        example=8589934592,  # 8GB in bytes
        description="Available Memory in Bytes",
    )
    percent: float = Field(
        ...,
        example=50.5,
        description="Percentage of Memory in Use",
        ge=0.0,
        le=100.0,
    )
    used: int = Field(
        ...,
        example=8589934592,  # 8GB in bytes
        description="Used Memory in Bytes",
    )
    free: int = Field(
        ...,
        example=8589934592,  # 8GB in bytes
        description="Free Memory in Bytes",
    )


# System Disk Usage Information Model
class SystemDisk(BaseModel):
    """
    System Disk Usage Information Model

    This Model Defines the Structure of the System Disk Usage Information.

    Attributes:
        total (int): Total Disk Space in Bytes
        used (int): Used Disk Space in Bytes
        free (int): Free Disk Space in Bytes
        percent (float): Percentage of Disk Space Used
    """

    # Model Fields
    total: int = Field(
        ...,
        example=107374182400,  # 100GB in bytes
        description="Total Disk Space in Bytes",
    )
    used: int = Field(
        ...,
        example=53687091200,  # 50GB in bytes
        description="Used Disk Space in Bytes",
    )
    free: int = Field(
        ...,
        example=53687091200,  # 50GB in bytes
        description="Free Disk Space in Bytes",
    )
    percent: float = Field(
        ...,
        example=50.0,
        description="Percentage of Disk Space Used",
        ge=0.0,
        le=100.0,
    )


# System Information Model
class SystemInfo(BaseModel):
    """
    System Information Model

    This Model Defines the Structure of the System Information.

    Attributes:
        hostname (str): System Hostname
        cpu_percent (float): Current CPU Usage Percentage
        memory (SystemMemory): Memory Usage Information
        disk (SystemDisk): Disk Usage Information
    """

    # Model Fields
    hostname: str = Field(
        ...,
        example="a2f460aba47d",
        description="System Hostname",
    )
    cpu_percent: float = Field(
        ...,
        example=25.5,
        description="Current CPU Usage Percentage",
        ge=0.0,
        le=100.0,
    )
    memory: SystemMemory = Field(
        ...,
        description="Memory Usage Information",
    )
    disk: SystemDisk = Field(
        ...,
        description="Disk Usage Information",
    )


# Health Response Model
class HealthResponse(BaseModel):
    """
    Health Response Model

    This Model Defines the Structure of the Health Check Response.

    Attributes:
        status (str): Current Status of the API
        app (str): Name of the Application
        version (str): Current Version of the API
        environment (str): Current Environment
        timestamp (str): ISO Format Timestamp of the Health Check
        system (SystemInfo): System Information and Metrics
    """

    # Model Fields
    status: str = Field(
        default="healthy",
        example="healthy",
        description="Current Status of the API",
        pattern="^(healthy|degraded|unhealthy)$",
    )
    app: str = Field(
        default="InitStack FastAPI Server",
        example="InitStack FastAPI Server",
        description="Name of the Application",
    )
    version: str = Field(
        default="0.1.0",
        example="0.1.0",
        description="Current Version of the API",
        pattern="^\\d+\\.\\d+\\.\\d+$",
    )
    environment: str = Field(
        default="development",
        example="production",
        description="Current Environment",
        pattern="^(development|staging|production)$",
    )
    timestamp: str = Field(
        ...,
        example="2025-07-21T05:27:32.123456Z",
        description="ISO Format Timestamp of the Health Check",
    )
    system: SystemInfo = Field(
        ...,
        description="System Information and Metrics",
    )

    # Get Memory Usage
    @classmethod
    def _get_memory_usage(cls) -> dict:
        """
        Get Current Memory Usage Information

        This Method Returns the Current Memory Usage Information.

        Returns:
            dict: Memory Usage Information
        """

        # Get Memory Usage
        memory: psutil.svmem = psutil.virtual_memory()

        # Return Memory Usage Information
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free,
        }

    # Get Disk Usage
    @classmethod
    def _get_disk_usage(cls) -> dict:
        """
        Get Current Disk Usage Information

        This Method Returns the Current Disk Usage Information.

        Returns:
            dict: Disk Usage Information
        """

        # Get Disk Usage
        usage: psutil.sdiskusage = psutil.disk_usage("/")

        # Return Disk Usage Information
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        }

    # Get Health Response
    @classmethod
    def get_health_response(cls) -> dict:
        """
        Get Health Response

        This Method Returns the Health Status of the API with System Information.

        Returns:
            dict: Health Status and System Information
        """

        # Get System Information
        system_info: dict = {
            "hostname": socket.gethostname(),
            "cpu_percent": psutil.cpu_percent(),
            "memory": cls._get_memory_usage(),
            "disk": cls._get_disk_usage(),
        }

        # Return Health Response with System Information
        return {
            "status": "healthy",
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.APP_ENV,
            "timestamp": datetime.datetime.now(tz=datetime.UTC),
            "system": system_info,
        }


# Exports
__all__: list[str] = ["HealthResponse"]
