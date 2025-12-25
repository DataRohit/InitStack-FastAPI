import datetime
import platform
from typing import Any

import psutil

from config.celery_app import celery_app


@celery_app.task(name="src.tasks.health.check_system_health")
def check_system_health() -> dict[str, Any]:
    """
    Check System Health And Return Metrics.

    Args:
        None

    Returns:
        dict[str, Any]: System Health Metrics.

    Raises:
        Exception: For Any Unexpected Errors During Health Check.
    """

    timestamp: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    cpu_percent: float = psutil.cpu_percent(interval=1)
    memory: psutil._pslinux.svmem = psutil.virtual_memory()  # ty:ignore[possibly-missing-attribute]
    disk: psutil._pslinux.sdiskusage = psutil.disk_usage("/")  # ty:ignore[possibly-missing-attribute]

    return {
        "status": "healthy",
        "timestamp": timestamp.isoformat(),
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
        "cpu": {
            "usage_percent": cpu_percent,
        },
        "memory": {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "usage_percent": memory.percent,
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "usage_percent": disk.percent,
        },
    }


__all__: list[str] = ["check_system_health"]
