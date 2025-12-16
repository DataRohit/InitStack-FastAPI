from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


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

    model_config: ConfigDict = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    error: str
    detail: str
    timestamp: datetime


__all__: list[str] = ["ErrorResponse"]
