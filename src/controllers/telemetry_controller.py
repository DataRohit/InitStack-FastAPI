from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi import Response
from fastapi import status
from opentelemetry.metrics import get_meter_provider
from opentelemetry.sdk.metrics import MeterProvider

from config.adapters.otel_metrics import get_prometheus_metrics
from config.logger import get_logger
from config.settings import settings
from src.schemas.telemetry import TelemetryHealthResponse

if TYPE_CHECKING:
    import logging


router: APIRouter = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get(
    path="/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get Metrics",
    description="Export Current Metrics In Prometheus Format",
    responses={
        200: {
            "description": "Metrics Exported Successfully",
            "content": {
                "text/plain": {
                    "example": '# HELP http_server_request_duration HTTP request duration in seconds\n# TYPE http_server_request_duration histogram\nhttp_server_request_duration_bucket{le="0.005"} 10\n',  # noqa: E501
                },
            },
        },
    },
)
async def get_metrics() -> Response:
    """
    Get Current Metrics In Prometheus Format.

    Args:
        None

    Returns:
        Response: Prometheus metrics in text format.

    Raises:
        Exception: For Any Unexpected Errors During Metrics Export.
    """

    logger: logging.Logger = get_logger(name="telemetry_controller.get_metrics")

    logger.info(msg="Metrics export requested")

    prometheus_metrics: bytes = get_prometheus_metrics()

    return Response(
        content=prometheus_metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8",
        status_code=status.HTTP_200_OK,
    )


@router.get(
    path="/health",
    response_model=TelemetryHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Telemetry Health Check",
    description="Check Telemetry System Health",
    responses={
        200: {
            "description": "Telemetry Health Check Successful",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "otel_metrics_enabled": True,
                        "elastic_apm_enabled": True,
                        "meter_provider_active": True,
                        "exporters": ["prometheus"],
                        "prometheus_endpoint": "/metrics",
                    },
                },
            },
        },
    },
)
async def get_telemetry_health() -> TelemetryHealthResponse:
    """
    Check Telemetry System Health.

    Args:
        None

    Returns:
        TelemetryHealthResponse: Telemetry health check response.

    Raises:
        Exception: For Any Unexpected Errors During Health Check.
    """

    logger: logging.Logger = get_logger(name="telemetry_controller.get_telemetry_health")

    logger.info(msg="Telemetry health check requested")

    meter_provider_active: bool = False
    exporters: list[str] = []

    try:
        meter_provider = get_meter_provider()

        if isinstance(meter_provider, MeterProvider):
            meter_provider_active = True
            exporters = ["prometheus"]

    except Exception as e:
        logger.warning(msg=f"Failed to get meter provider: {e!s}")

    status_value: str = "healthy" if settings.otel_metrics_enabled and meter_provider_active else "degraded"

    response: TelemetryHealthResponse = TelemetryHealthResponse(
        status=status_value,
        otel_metrics_enabled=settings.otel_metrics_enabled,
        elastic_apm_enabled=settings.telemetry_enabled,
        meter_provider_active=meter_provider_active,
        exporters=exporters,
        prometheus_endpoint=settings.otel_prometheus_endpoint,
    )

    return response


@router.get(
    path=settings.otel_prometheus_endpoint,
    status_code=status.HTTP_200_OK,
    summary="Prometheus Metrics",
    description="Get Metrics In Prometheus Format",
    responses={
        200: {
            "description": "Prometheus Metrics",
            "content": {
                "text/plain": {
                    "example": '# HELP http_server_request_duration HTTP request duration in seconds\n# TYPE http_server_request_duration histogram\nhttp_server_request_duration_bucket{le="0.005"} 10\n',  # noqa: E501
                },
            },
        },
    },
)
async def get_prometheus_metrics_endpoint() -> Response:
    """
    Get Metrics In Prometheus Format.

    Args:
        None

    Returns:
        Response: Prometheus metrics in text format.

    Raises:
        Exception: For Any Unexpected Errors During Metrics Export.
    """

    logger: logging.Logger = get_logger(name="telemetry_controller.get_prometheus_metrics_endpoint")

    logger.debug(msg="Prometheus metrics requested")

    prometheus_metrics: bytes = get_prometheus_metrics()

    return Response(
        content=prometheus_metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8",
        status_code=status.HTTP_200_OK,
    )


__all__: list[str] = ["router"]
