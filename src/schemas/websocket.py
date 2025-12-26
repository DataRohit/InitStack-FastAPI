from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class WebSocketPingRequest(BaseModel):
    """WebSocket Ping Request Model.

    Inherits:
        BaseModel

    Attributes:
        message (str): Message to echo back in the pong response.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    message: str = Field(
        default=...,
        description="Message to echo back in the pong response.",
        examples=["Hello, WebSocket!", "Ping", "Test message"],
        min_length=1,
        max_length=1000,
    )


class WebSocketPongResponse(BaseModel):
    """WebSocket Pong Response Model.

    Inherits:
        BaseModel

    Attributes:
        status (str): Response status indicator.
        message (str): Response message.
        timestamp (datetime): Response timestamp.
        echo (str): Echoed message from the ping request.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    status: str = Field(
        default=...,
        description="Response status indicator.",
        examples=["success", "error"],
    )
    message: str = Field(
        default=...,
        description="Response message.",
        examples=["Pong", "Message received", "Error processing request"],
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp when the pong response was generated.",
        examples=["2025-12-26T10:42:56Z"],
    )
    echo: str = Field(
        default=...,
        description="Echoed message from the ping request.",
        examples=["Hello, WebSocket!", "Ping", "Test message"],
    )


class WebSocketErrorResponse(BaseModel):
    """WebSocket Error Response Model.

    Inherits:
        BaseModel

    Attributes:
        status (str): Response status indicator (always 'error').
        message (str): Error message.
        timestamp (datetime): Error timestamp.
        detail (str): Detailed error information.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    status: str = Field(
        default="error",
        description="Response status indicator.",
        examples=["error"],
    )
    message: str = Field(
        default=...,
        description="Error message.",
        examples=["Invalid JSON format", "Validation error", "Connection error"],
    )
    timestamp: datetime = Field(
        default=...,
        description="Timestamp when the error response was generated.",
        examples=["2025-12-26T10:42:56Z"],
    )
    detail: str = Field(
        default=...,
        description="Detailed error information.",
        examples=[
            "Expected JSON object with 'message' field",
            "Message field is required",
            "Message exceeds maximum length",
        ],
    )


__all__: list[str] = [
    "WebSocketErrorResponse",
    "WebSocketPingRequest",
    "WebSocketPongResponse",
]
