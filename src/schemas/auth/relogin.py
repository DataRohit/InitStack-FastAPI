from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.schemas.auth.login import LoginResponse


class ReloginRequest(BaseModel):
    """Relogin Request Schema.

    Inherits:
        BaseModel

    Attributes:
        refresh_token (str): JWT refresh token.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    refresh_token: str = Field(
        default=...,
        description="JWT refresh token.",
        min_length=1,
        examples=["<refresh_token>"],
    )


class ReloginResponse(LoginResponse):
    """Relogin Response Schema.

    Inherits:
        LoginResponse
    """


__all__: list[str] = ["ReloginRequest", "ReloginResponse"]
