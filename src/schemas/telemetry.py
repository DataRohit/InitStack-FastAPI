from pydantic import BaseModel
from pydantic import Field


class TelemetryHealthResponse(BaseModel):
    """Telemetry Health Check Response Schema.

    Attributes:
        status (str): Overall telemetry health status.
        otel_metrics_enabled (bool): Whether OpenTelemetry metrics are enabled.
        elastic_apm_enabled (bool): Whether Elastic APM is enabled.
        meter_provider_active (bool): Whether meter provider is active.
        exporters (list[str]): List of active exporters.
        prometheus_endpoint (str): Prometheus endpoint path.

    Properties:
        None

    Methods:
        None
    """

    status: str = Field(description="Telemetry Health Status")
    otel_metrics_enabled: bool = Field(description="Opentelemetry Metrics Enabled")
    elastic_apm_enabled: bool = Field(description="Elastic Apm Enabled")
    meter_provider_active: bool = Field(description="Meter Provider Active")
    exporters: list[str] = Field(description="Active Exporters")
    prometheus_endpoint: str = Field(description="Prometheus Endpoint Path")


__all__: list[str] = [
    "TelemetryHealthResponse",
]
