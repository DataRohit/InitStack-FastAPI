# ruff: noqa: PLW0603

from typing import TYPE_CHECKING

from config.adapters.otel_metrics import get_meter
from config.settings import settings

if TYPE_CHECKING:
    from opentelemetry.metrics import Counter
    from opentelemetry.metrics import Histogram
    from opentelemetry.metrics import Meter
    from opentelemetry.metrics import UpDownCounter


_meter: Meter | None = None


def _get_meter() -> Meter:
    """
    Get Or Create Meter Instance.

    Args:
        None

    Returns:
        Meter: Meter instance for creating metrics.

    Raises:
        None
    """

    global _meter

    if _meter is None:
        _meter = get_meter(name="initstack.metrics")

    return _meter


http_request_duration_histogram: Histogram | None = None
http_request_counter: Counter | None = None
http_active_requests_gauge: UpDownCounter | None = None
http_request_size_histogram: Histogram | None = None
http_response_size_histogram: Histogram | None = None
db_query_duration_histogram: Histogram | None = None
db_connection_pool_gauge: UpDownCounter | None = None
db_query_counter: Counter | None = None
redis_operation_duration_histogram: Histogram | None = None
redis_operation_counter: Counter | None = None
redis_connection_pool_gauge: UpDownCounter | None = None
rabbitmq_message_duration_histogram: Histogram | None = None
rabbitmq_message_counter: Counter | None = None
rabbitmq_queue_size_gauge: UpDownCounter | None = None
auth_login_counter: Counter | None = None
auth_token_generation_duration: Histogram | None = None
rate_limit_exceeded_counter: Counter | None = None


def initialize_metrics() -> None:
    """
    Initialize All Metrics.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    meter: Meter = _get_meter()

    global http_request_duration_histogram
    http_request_duration_histogram = meter.create_histogram(
        name="http.server.request.duration",
        description="HTTP request duration in seconds",
        unit="s",
    )

    global http_request_counter
    http_request_counter = meter.create_counter(
        name="http.server.request.count",
        description="Total HTTP requests",
        unit="1",
    )

    global http_active_requests_gauge
    http_active_requests_gauge = meter.create_up_down_counter(
        name="http.server.active_requests",
        description="Current active HTTP requests",
        unit="1",
    )

    global http_request_size_histogram
    http_request_size_histogram = meter.create_histogram(
        name="http.server.request.size",
        description="HTTP request body size in bytes",
        unit="By",
    )

    global http_response_size_histogram
    http_response_size_histogram = meter.create_histogram(
        name="http.server.response.size",
        description="HTTP response body size in bytes",
        unit="By",
    )

    global db_query_duration_histogram
    db_query_duration_histogram = meter.create_histogram(
        name="db.client.operation.duration",
        description="Database query duration in seconds",
        unit="s",
    )

    global db_connection_pool_gauge
    db_connection_pool_gauge = meter.create_up_down_counter(
        name="db.client.connections.usage",
        description="Active database connections",
        unit="1",
    )

    global db_query_counter
    db_query_counter = meter.create_counter(
        name="db.client.operation.count",
        description="Total database queries",
        unit="1",
    )

    global redis_operation_duration_histogram
    redis_operation_duration_histogram = meter.create_histogram(
        name="redis.client.operation.duration",
        description="Redis operation duration in seconds",
        unit="s",
    )

    global redis_operation_counter
    redis_operation_counter = meter.create_counter(
        name="redis.client.operation.count",
        description="Total Redis operations",
        unit="1",
    )

    global redis_connection_pool_gauge
    redis_connection_pool_gauge = meter.create_up_down_counter(
        name="redis.client.connections.usage",
        description="Active Redis connections",
        unit="1",
    )

    global rabbitmq_message_duration_histogram
    rabbitmq_message_duration_histogram = meter.create_histogram(
        name="messaging.process.duration",
        description="Message processing duration in seconds",
        unit="s",
    )

    global rabbitmq_message_counter
    rabbitmq_message_counter = meter.create_counter(
        name="messaging.process.count",
        description="Total messages processed",
        unit="1",
    )

    global rabbitmq_queue_size_gauge
    rabbitmq_queue_size_gauge = meter.create_up_down_counter(
        name="messaging.queue.messages",
        description="Current queue size",
        unit="1",
    )

    global auth_login_counter
    auth_login_counter = meter.create_counter(
        name="auth.login.count",
        description="Login attempts",
        unit="1",
    )

    global auth_token_generation_duration
    auth_token_generation_duration = meter.create_histogram(
        name="auth.token.generation.duration",
        description="Token generation duration in seconds",
        unit="s",
    )

    global rate_limit_exceeded_counter
    rate_limit_exceeded_counter = meter.create_counter(
        name="http.server.rate_limit.exceeded",
        description="Rate limit violations",
        unit="1",
    )


def record_http_request(  # noqa: PLR0913
    method: str,
    endpoint: str,
    status: int,
    duration: float,
    request_size: int = 0,
    response_size: int = 0,
) -> None:
    """
    Record Http Request Metrics.

    Args:
        method (str): HTTP method.
        endpoint (str): Request endpoint.
        status (int): Response status code.
        duration (float): Request duration in seconds.
        request_size (int): Request body size in bytes.
        response_size (int): Response body size in bytes.

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    if http_request_duration_histogram:
        http_request_duration_histogram.record(
            amount=duration,
            attributes={
                "http.request.method": method,
                "url.path": endpoint,
                "http.response.status_code": status,
            },
        )

    if http_request_counter:
        http_request_counter.add(
            amount=1,
            attributes={
                "http.request.method": method,
                "url.path": endpoint,
                "http.response.status_code": status,
            },
        )

    if request_size > 0 and http_request_size_histogram:
        http_request_size_histogram.record(
            amount=request_size,
            attributes={
                "http.request.method": method,
                "url.path": endpoint,
            },
        )

    if response_size > 0 and http_response_size_histogram:
        http_response_size_histogram.record(
            amount=response_size,
            attributes={
                "http.request.method": method,
                "url.path": endpoint,
                "http.response.status_code": status,
            },
        )


def record_db_query(operation: str, duration: float, table: str = "") -> None:
    """
    Record Database Query Metrics.

    Args:
        operation (str): Database operation type (SELECT, INSERT, UPDATE, DELETE).
        duration (float): Query duration in seconds.
        table (str): Table name.

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    attributes: dict[str, str] = {"db.operation": operation}

    if table:
        attributes["db.sql.table"] = table

    if db_query_duration_histogram:
        db_query_duration_histogram.record(amount=duration, attributes=attributes)

    if db_query_counter:
        db_query_counter.add(amount=1, attributes=attributes)


def record_redis_operation(command: str, duration: float) -> None:
    """
    Record Redis Operation Metrics.

    Args:
        command (str): Redis command.
        duration (float): Operation duration in seconds.

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    attributes: dict[str, str] = {"db.operation": command}

    if redis_operation_duration_histogram:
        redis_operation_duration_histogram.record(amount=duration, attributes=attributes)

    if redis_operation_counter:
        redis_operation_counter.add(amount=1, attributes=attributes)


def record_rabbitmq_message(queue: str, status: str, duration: float) -> None:
    """
    Record Rabbitmq Message Metrics.

    Args:
        queue (str): Queue name.
        status (str): Message processing status (success, error).
        duration (float): Processing duration in seconds.

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    attributes: dict[str, str] = {
        "messaging.destination.name": queue,
        "messaging.operation": "process",
        "messaging.operation.status": status,
    }

    if rabbitmq_message_duration_histogram:
        rabbitmq_message_duration_histogram.record(amount=duration, attributes=attributes)

    if rabbitmq_message_counter:
        rabbitmq_message_counter.add(amount=1, attributes=attributes)


def increment_active_requests() -> None:
    """
    Increment Active Requests Gauge.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    if http_active_requests_gauge:
        http_active_requests_gauge.add(amount=1)


def decrement_active_requests() -> None:
    """
    Decrement Active Requests Gauge.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    if http_active_requests_gauge:
        http_active_requests_gauge.add(amount=-1)


def record_auth_login(status: str) -> None:
    """
    Record Auth Login Attempt.

    Args:
        status (str): Login status (success, failed, invalid).

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    if auth_login_counter:
        auth_login_counter.add(amount=1, attributes={"auth.login.status": status})


def record_auth_token_generation(duration: float, token_type: str) -> None:
    """
    Record Auth Token Generation Duration.

    Args:
        duration (float): Token generation duration in seconds.
        token_type (str): Token type (access, refresh).

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    if auth_token_generation_duration:
        auth_token_generation_duration.record(
            amount=duration,
            attributes={"auth.token.type": token_type},
        )


def record_rate_limit_exceeded(client_ip: str) -> None:
    """
    Record Rate Limit Exceeded Event.

    Args:
        client_ip (str): Client IP address.

    Returns:
        None

    Raises:
        None
    """

    if not settings.otel_metrics_enabled:
        return

    if rate_limit_exceeded_counter:
        rate_limit_exceeded_counter.add(amount=1, attributes={"client.address": client_ip})


__all__: list[str] = [
    "decrement_active_requests",
    "increment_active_requests",
    "initialize_metrics",
    "record_auth_login",
    "record_auth_token_generation",
    "record_db_query",
    "record_http_request",
    "record_rabbitmq_message",
    "record_rate_limit_exceeded",
    "record_redis_operation",
]
