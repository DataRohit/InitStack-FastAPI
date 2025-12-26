import socket
from typing import TYPE_CHECKING

from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.elasticsearch import ElasticsearchInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import get_meter_provider
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import REGISTRY
from prometheus_client.openmetrics.exposition import generate_latest

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging
    from collections.abc import Sequence

    from opentelemetry import metrics
    from opentelemetry.metrics import Meter


_meter_provider: MeterProvider | None = None


def setup_resource() -> Resource:
    """
    Configure Service Resource With Attributes.

    Args:
        None

    Returns:
        Resource: Configured resource with service attributes.

    Raises:
        Exception: For Any Unexpected Errors During Resource Setup.
    """

    hostname: str = socket.gethostname()

    resource_attributes: dict[str, str] = {
        "service.name": settings.otel_service_name,
        "service.version": settings.app_version,
        "service.instance.id": f"{settings.otel_service_name}-{hostname}",
        "deployment.environment": settings.environment,
        "host.name": hostname,
    }

    if settings.otel_resource_attributes:
        resource_attributes.update(settings.otel_resource_attributes)

    resource: Resource = Resource.create(attributes=resource_attributes)

    return resource


def setup_meter_provider() -> MeterProvider:
    """
    Initialize Meter Provider With Prometheus Exporter.

    Args:
        None

    Returns:
        MeterProvider: Configured meter provider with Prometheus exporter.

    Raises:
        Exception: For Any Unexpected Errors During Meter Provider Setup.
    """

    logger: logging.Logger = get_logger(name="otel_metrics.setup_meter_provider")

    resource: Resource = setup_resource()

    prometheus_reader: PrometheusMetricReader = PrometheusMetricReader()

    meter_provider: MeterProvider = MeterProvider(
        resource=resource,
        metric_readers=[prometheus_reader],
    )

    set_meter_provider(meter_provider=meter_provider)

    logger.info(
        msg="Meter provider initialized with Prometheus exporter",
        extra={
            "service_name": settings.otel_service_name,
            "service_version": settings.app_version,
            "environment": settings.environment,
        },
    )

    return meter_provider


def get_meter(name: str) -> Meter:
    """
    Get Meter Instance For Creating Metrics.

    Args:
        name (str): Meter name (typically module or component name).

    Returns:
        Meter: Meter instance for creating metrics.

    Raises:
        Exception: For Any Unexpected Errors During Meter Retrieval.
    """

    meter_provider: metrics.MeterProvider = get_meter_provider()

    meter: Meter = meter_provider.get_meter(name=name, version=settings.app_version)

    return meter


def setup_otel_metrics() -> None:
    """
    Main Setup Function For OpenTelemetry Metrics.

    Args:
        None

    Returns:
        None

    Raises:
        Exception: For Any Unexpected Errors During OpenTelemetry Metrics Setup.
    """

    logger: logging.Logger = get_logger(name="otel_metrics.setup")

    if not settings.otel_metrics_enabled:
        logger.info(msg="OpenTelemetry metrics disabled")
        return

    try:
        global _meter_provider  # noqa: PLW0603
        _meter_provider = setup_meter_provider()

        logger.info(
            msg="OpenTelemetry metrics initialized successfully",
            extra={
                "prometheus_endpoint": settings.otel_prometheus_endpoint,
                "service_name": settings.otel_service_name,
                "metrics_interval": settings.otel_metrics_export_interval,
            },
        )

    except Exception as e:
        logger.exception(msg=f"Failed to initialize OpenTelemetry metrics: {e!s}")


def get_prometheus_metrics() -> bytes:
    """
    Get Current Metrics In Prometheus Format.

    Args:
        None

    Returns:
        bytes: Metrics in Prometheus text format.

    Raises:
        Exception: For Any Unexpected Errors During Metrics Retrieval.
    """

    meter_provider: metrics.MeterProvider = get_meter_provider()

    if not isinstance(meter_provider, MeterProvider):
        return b""

    metric_readers: Sequence = meter_provider._sdk_config.metric_readers  # noqa: SLF001

    for reader in metric_readers:
        if isinstance(reader, PrometheusMetricReader):
            try:
                return generate_latest(REGISTRY)
            except Exception:
                return b""

    return b""


def setup_auto_instrumentation() -> None:  # noqa: C901, PLR0912, PLR0915
    """
    Setup Auto Instrumentation For All Services.

    Args:
        None

    Returns:
        None

    Raises:
        Exception: For Any Unexpected Errors During Auto Instrumentation Setup.
    """

    logger: logging.Logger = get_logger(name="otel_metrics.setup_auto_instrumentation")

    if not settings.otel_metrics_enabled:
        logger.info(msg="OpenTelemetry auto-instrumentation disabled")
        return

    try:
        try:
            FastAPIInstrumentor().instrument()
            logger.info(msg="FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning(msg=f"Failed to instrument FastAPI: {e!s}")

        if settings.redis_enabled:
            try:
                RedisInstrumentor().instrument()
                logger.info(msg="Redis instrumentation enabled")
            except Exception as e:
                logger.warning(msg=f"Failed to instrument Redis: {e!s}")

        if settings.postgresql_enabled:
            try:
                SQLAlchemyInstrumentor().instrument()
                logger.info(msg="SQLAlchemy instrumentation enabled")
            except Exception as e:
                logger.warning(msg=f"Failed to instrument SQLAlchemy: {e!s}")

        try:
            HTTPXClientInstrumentor().instrument()
            logger.info(msg="HTTPX instrumentation enabled")
        except Exception as e:
            logger.warning(msg=f"Failed to instrument HTTPX: {e!s}")

        try:
            RequestsInstrumentor().instrument()
            logger.info(msg="Requests instrumentation enabled")
        except Exception as e:
            logger.warning(msg=f"Failed to instrument Requests: {e!s}")

        if settings.elasticsearch_enabled:
            try:
                ElasticsearchInstrumentor().instrument()
                logger.info(msg="Elasticsearch instrumentation enabled")
            except Exception as e:
                logger.warning(msg=f"Failed to instrument Elasticsearch: {e!s}")

        try:
            CeleryInstrumentor().instrument()
            logger.info(msg="Celery instrumentation enabled")
        except Exception as e:
            logger.warning(msg=f"Failed to instrument Celery: {e!s}")

        if settings.postgresql_enabled:
            try:
                PsycopgInstrumentor().instrument()
                logger.info(msg="Psycopg instrumentation enabled")
            except Exception as e:
                logger.warning(msg=f"Failed to instrument Psycopg: {e!s}")

        logger.info(msg="Auto-instrumentation setup completed")

    except Exception as e:
        logger.exception(msg=f"Failed to setup auto-instrumentation: {e!s}")


__all__: list[str] = [
    "get_meter",
    "get_prometheus_metrics",
    "setup_auto_instrumentation",
    "setup_otel_metrics",
    "setup_resource",
]
