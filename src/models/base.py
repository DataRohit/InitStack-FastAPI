from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ErrorResponse(BaseModel):
    """Standard Error Response Payload.

    Inherits:
        BaseModel

    Attributes:
        error (str): High-level error message.
        detail (str): Detailed error information.
        timestamp (datetime): Error timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "examples": [
                {
                    "error": "Not Found",
                    "detail": "HTTP 404",
                    "timestamp": "2025-01-01T12:34:56Z",
                },
                {
                    "error": "Unauthorized",
                    "detail": "HTTP 401",
                    "timestamp": "2025-01-01T12:34:56Z",
                },
                {
                    "error": "Forbidden",
                    "detail": "HTTP 403",
                    "timestamp": "2025-01-01T12:34:56Z",
                },
                {
                    "error": "Validation Error",
                    "detail": (
                        "1 validation error for Request\nbody -> name\n  Field required (type=value_error.missing)"
                    ),
                    "timestamp": "2025-01-01T12:34:56Z",
                },
                {
                    "error": "Internal Server Error",
                    "detail": "An Unexpected Error Occurred",
                    "timestamp": "2025-01-01T12:34:56Z",
                },
            ],
        },
    )

    error: str = Field(
        default=...,
        description="High-level error message.",
        examples=["Validation Error", "Not Found", "Internal Server Error"],
    )
    detail: str = Field(
        default=...,
        description=(
            "Detailed error information. For HTTP exceptions this is typically "
            "'HTTP <status_code>'; for validation errors this contains the validation "
            "exception string; for unhandled errors it is a generic message."
        ),
        examples=[
            "HTTP 404",
            "HTTP 401",
            "HTTP 403",
            "1 validation error for Request\nbody -> name\n  Field required (type=value_error.missing)",
            "An Unexpected Error Occurred",
        ],
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp indicating when the error response was generated.",
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = ["ErrorResponse"]
