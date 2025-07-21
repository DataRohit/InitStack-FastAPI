# Standard Library Imports
from typing import Any

import psutil

# Third-Party Imports
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# Local Imports
from src.models.health import HealthResponse

# Constants
USAGE_THRESHOLD: int = 90

# Initialize Router
router = APIRouter(
    prefix="/health",
    tags=["Health Check"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error!"}}},
        },
    },
)


# Health Check Endpoint
@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Health Check Endpoint",
    description="""
    Returns The Health Status of the API along with System Metrics.

    This Endpoint Provides Detailed Information About:
    - API Status (healthy/degraded/unhealthy)
    - Application Metadata (name, version, environment)
    - System Metrics (CPU, memory, disk usage)
    - Timestamp of The Health Check
    """,
    name="Health Check",
    response_model=HealthResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Health Check",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "app": "InitStack FastAPI Server",
                        "version": "0.1.0",
                        "environment": "production",
                        "timestamp": "2025-07-21T05:30:00.000000+00:00",
                        "system": {
                            "hostname": "a2f460aba47d",
                            "cpu_percent": 15.5,
                            "memory": {
                                "total": 17179869184,
                                "available": 12884901888,
                                "percent": 25.0,
                                "used": 4294967296,
                                "free": 12884901888,
                            },
                            "disk": {
                                "total": 107374182400,
                                "used": 53687091200,
                                "free": 53687091200,
                                "percent": 50.0,
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Service Unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "app": "InitStack FastAPI Server",
                        "version": "0.1.0",
                        "environment": "production",
                        "timestamp": "2025-07-21T05:30:00.000000+00:00",
                        "system": {
                            "hostname": "a2f460aba47d",
                            "cpu_percent": 95.5,
                            "memory": {
                                "total": 17179869184,
                                "available": 1073741824,
                                "percent": 93.8,
                                "used": 16106127360,
                                "free": 1073741824,
                            },
                            "disk": {
                                "total": 107374182400,
                                "used": 105656195072,
                                "free": 1717987328,
                                "percent": 98.4,
                            },
                        },
                    },
                },
            },
        },
    },
)
async def health_check() -> dict[str, Any]:
    """
    Health Check Endpoint

    This Endpoint Provides a Comprehensive Health Status of the API and System Metrics.

    It's Designed to be Used by:
    - Load Balancers for Health Checks
    - Monitoring Systems
    - Deployment Pipelines
    - System Administrators

    The Response Includes:
    - API Status (healthy/degraded/unhealthy)
    - Application Metadata
    - System Resource Usage (CPU, memory, disk)
    - Timestamp of the Health Check

    Returns:
        dict[str, Any]: Detailed Health Status and System Metrics

    Raises:
        HTTPException: If the Service is Unhealthy (503) or Encounters an Error (500)
    """

    try:
        # Get the Health Status
        health_data = HealthResponse.get_health_response()

        # If Any System Metrics Exceed the Usage Threshold
        if (
            health_data["system"]["memory"]["percent"] > USAGE_THRESHOLD
            or health_data["system"]["disk"]["percent"] > USAGE_THRESHOLD
            or health_data["system"]["cpu_percent"] > USAGE_THRESHOLD
        ):
            # Set the Status to Degraded
            health_data["status"] = "degraded"

            # Return a 503 Error if the Service is Degraded
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_data,
            )

    except psutil.Error:
        # Return a 500 Error if Error in System Metrics
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error Collecting System Metrics!"},
        )

    except Exception:  # noqa: BLE001
        # Return a 500 Error if Something Goes Wrong
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error!"},
        )

    # Return the Health Data
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=health_data,
    )


# Exports
__all__: list[str] = ["router"]
