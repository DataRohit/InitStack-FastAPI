from datetime import datetime
from typing import Any

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


class ValidationErrorItem(BaseModel):
    """Validation Error Item.

    Inherits:
        BaseModel

    Attributes:
        path (str): Location of the invalid field (e.g. 'body.email').
        message (str): Human-readable validation error message.
        type (str): Error type identifier.
        meta (dict[str, Any] | None): Optional metadata from the validator.

    Properties:
        None

    Methods:
        None
    """

    path: str = Field(
        default=...,
        description="Location of the invalid field.",
        examples=["body.email", "body.password", "query.page"],
    )
    message: str = Field(
        default=...,
        description="Human-readable validation error message.",
        examples=["Invalid email format", "Field required"],
    )
    type: str = Field(
        default=...,
        description="Validation error type.",
        examples=["value_error", "missing"],
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Optional validation metadata.",
        examples=[{"min_length": 8}],
    )


class ValidationErrorResponse(BaseModel):
    """Validation Error Response Payload.

    Inherits:
        BaseModel

    Attributes:
        error (str): High-level error message.
        errors (list[ValidationErrorItem]): Field-level validation errors.
        timestamp (datetime): Error timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    error: str = Field(
        default="Validation Error",
        description="High-level error message.",
        examples=["Validation Error"],
    )
    errors: list[ValidationErrorItem] = Field(
        default=...,
        description="List of validation errors.",
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp indicating when the error response was generated.",
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = [
    "ErrorResponse",
    "ValidationErrorItem",
    "ValidationErrorResponse",
]
