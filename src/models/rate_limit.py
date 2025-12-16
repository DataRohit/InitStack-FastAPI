from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RateLimitConfig(BaseModel):
    """Rate Limit Configuration Model.

    Inherits:
        BaseModel

    Attributes:
        enabled (bool): Whether rate limiting is enabled.
        requests_per_minute (int): Maximum requests per minute per client.
        burst_size (int): Burst size for rate limiting.
        window_size (int): Rate limit window size in seconds.
        redis_key_prefix (str): Redis key prefix for rate limiting.
        redis_key_expiry (int): Redis key expiry in seconds.
        exempt_ips (list[str]): IP addresses exempt from rate limiting.
        header_enabled (bool): Include rate limit headers in responses.
        retry_after_header (bool): Include Retry-After header when rate limited.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    enabled: bool = Field(
        description="Whether rate limiting is enabled",
        examples=[True, False],
    )
    requests_per_minute: int = Field(
        description="Maximum requests per minute per client",
        examples=[60, 100, 1000],
        ge=1,
        le=10000,
    )
    burst_size: int = Field(
        description="Burst size for rate limiting",
        examples=[10, 20, 50],
        ge=1,
        le=1000,
    )
    window_size: int = Field(
        description="Rate limit window size in seconds",
        examples=[60, 300, 3600],
        ge=1,
        le=86400,
    )
    redis_key_prefix: str = Field(
        description="Redis key prefix for rate limiting",
        examples=["rate_limit", "api_rate_limit", "rl"],
    )
    redis_key_expiry: int = Field(
        description="Redis key expiry in seconds",
        examples=[3600, 7200, 86400],
        ge=60,
        le=604800,
    )
    exempt_ips: list[str] = Field(
        description="IP addresses exempt from rate limiting",
        examples=[["127.0.0.1", "::1"], ["10.0.0.0/8", "192.168.0.0/16"]],
    )
    header_enabled: bool = Field(
        description="Include rate limit headers in responses",
        examples=[True, False],
    )
    retry_after_header: bool = Field(
        description="Include Retry-After header when rate limited",
        examples=[True, False],
    )


class RateLimitStatus(BaseModel):
    """Rate Limit Status Model.

    Inherits:
        BaseModel

    Attributes:
        client_id (str): Client identifier hash.
        client_ip (str): Client IP address.
        current_count (int): Current request count in window.
        limit (int): Request limit per window.
        remaining (int): Remaining requests in current window.
        reset_time (datetime): Window reset time.
        is_exempt (bool): Whether client is exempt from rate limiting.
        window_start (datetime): Current window start time.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    client_id: str = Field(
        description="Client identifier hash",
        examples=["a1b2c3d4e5f6g7h8", "x9y8z7w6v5u4t3s2"],
    )
    client_ip: str = Field(
        description="Client IP address",
        examples=["192.168.1.100", "127.0.0.1", "10.0.0.5"],
    )
    current_count: int = Field(
        description="Current request count in window",
        examples=[5, 25, 59],
        ge=0,
    )
    limit: int = Field(
        description="Request limit per window",
        examples=[60, 100, 1000],
        ge=1,
    )
    remaining: int = Field(
        description="Remaining requests in current window",
        examples=[55, 35, 1],
        ge=0,
    )
    reset_time: datetime = Field(
        description="Window reset time",
        examples=["2025-01-01T12:35:00Z"],
    )
    is_exempt: bool = Field(
        description="Whether client is exempt from rate limiting",
        examples=[False, True],
    )
    window_start: datetime = Field(
        description="Current window start time",
        examples=["2025-01-01T12:34:00Z"],
    )


class RateLimitTestResult(BaseModel):
    """Rate Limit Test Result Model.

    Inherits:
        BaseModel

    Attributes:
        request_number (int): Request number in test sequence.
        allowed (bool): Whether request was allowed.
        status_code (int): HTTP status code.
        headers (dict[str, str]): Response headers.
        duration_ms (float): Request duration in milliseconds.
        error (str | None): Error message if request failed.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    request_number: int = Field(
        description="Request number in test sequence",
        examples=[1, 25, 61],
        ge=1,
    )
    allowed: bool = Field(
        description="Whether request was allowed",
        examples=[True, False],
    )
    status_code: int = Field(
        description="HTTP status code",
        examples=[200, 429, 500, 0],
        ge=0,
        le=599,
    )
    headers: dict[str, str] = Field(
        description="Response headers",
        examples=[
            {"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "59"},
            {"Retry-After": "30"},
            {},
        ],
    )
    duration_ms: float = Field(
        description="Request duration in milliseconds",
        examples=[12.34, 5.67, 1000.0],
        ge=0.0,
    )
    error: str | None = Field(
        default=None,
        description="Error message if request failed",
        examples=[None, "Request failed: connection timeout", "Rate limit exceeded"],
    )


class RateLimitStatusResponse(BaseModel):
    """Rate Limit Status Response Model.

    Inherits:
        BaseModel

    Attributes:
        rate_limiting_enabled (bool): Whether rate limiting is enabled.
        redis_available (bool): Whether Redis is available for rate limiting.
        config (RateLimitConfig): Rate limiting configuration.
        current_status (RateLimitStatus | None): Current rate limit status for client.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    rate_limiting_enabled: bool = Field(
        description="Whether rate limiting is enabled",
        examples=[True, False],
    )
    redis_available: bool = Field(
        description="Whether Redis is available for rate limiting",
        examples=[True, False],
    )
    config: RateLimitConfig = Field(
        description="Rate limiting configuration",
    )
    current_status: RateLimitStatus | None = Field(
        default=None,
        description="Current rate limit status for client",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:30Z"],
    )


class RateLimitTestResponse(BaseModel):
    """Rate Limit Test Response Model.

    Inherits:
        BaseModel

    Attributes:
        rate_limiting_enabled (bool): Whether rate limiting is enabled.
        redis_available (bool): Whether Redis is available for rate limiting.
        test_requests_sent (int): Number of test requests sent.
        requests_allowed (int): Number of requests allowed.
        requests_blocked (int): Number of requests blocked.
        first_block_at_request (int | None): Request number where first block occurred.
        total_test_duration_ms (float): Total test duration in milliseconds.
        results (list[RateLimitTestResult]): Individual test results.
        timestamp (datetime): Response timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    rate_limiting_enabled: bool = Field(
        description="Whether rate limiting is enabled",
        examples=[True, False],
    )
    redis_available: bool = Field(
        description="Whether Redis is available for rate limiting",
        examples=[True, False],
    )
    test_requests_sent: int = Field(
        description="Number of test requests sent",
        examples=[65, 100, 200],
        ge=1,
    )
    requests_allowed: int = Field(
        description="Number of requests allowed",
        examples=[60, 65, 100],
        ge=0,
    )
    requests_blocked: int = Field(
        description="Number of requests blocked",
        examples=[5, 0, 100],
        ge=0,
    )
    first_block_at_request: int | None = Field(
        default=None,
        description="Request number where first block occurred",
        examples=[61, None, 101],
        ge=1,
    )
    total_test_duration_ms: float = Field(
        description="Total test duration in milliseconds",
        examples=[1234.56, 987.65, 2500.0],
        ge=0.0,
    )
    results: list[RateLimitTestResult] = Field(
        description="Individual test results",
    )
    timestamp: datetime = Field(
        description="Response timestamp",
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = [
    "RateLimitConfig",
    "RateLimitStatus",
    "RateLimitStatusResponse",
    "RateLimitTestResponse",
    "RateLimitTestResult",
]
