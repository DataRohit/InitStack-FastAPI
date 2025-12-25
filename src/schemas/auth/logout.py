from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class LogoutResponse(BaseModel):
    """Logout Response Schema.

    Inherits:
        BaseModel

    Attributes:
        message (str): Logout confirmation message.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    message: str = Field(
        default=...,
        description="Logout confirmation message.",
        examples=["Logged out successfully"],
    )


__all__: list[str] = ["LogoutResponse"]
