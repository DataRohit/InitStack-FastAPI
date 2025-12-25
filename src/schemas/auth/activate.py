from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ActivateAccountResponse(BaseModel):
    """Activate Account Response Schema.

    Inherits:
        BaseModel

    Attributes:
        id (str): User identifier.
        username (str): Username.
        email (str): Email address.
        first_name (str): First name.
        last_name (str): Last name.
        is_active (bool): Whether user account is active.
        is_admin (bool): Whether user has admin privileges.
        is_superuser (bool): Whether user has superuser privileges.
        created_at (datetime): Creation timestamp.
        updated_at (datetime | None): Update timestamp.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    id: str = Field(
        default=...,
        description="User identifier.",
        examples=["b2c1f7c6-1e27-4f2e-9b92-27d0f0f7c9a1"],
    )
    username: str = Field(
        default=...,
        description="Unique username.",
        examples=["john_doe"],
    )
    email: str = Field(
        default=...,
        description="Unique email address.",
        examples=["user@example.com"],
    )
    first_name: str = Field(
        default=...,
        description="User's first name.",
        examples=["John"],
    )
    last_name: str = Field(
        default=...,
        description="User's last name.",
        examples=["Doe"],
    )
    is_active: bool = Field(
        default=...,
        description="Whether user account is active.",
        examples=[True],
    )
    is_admin: bool = Field(
        default=...,
        description="Whether user has admin privileges.",
        examples=[False],
    )
    is_superuser: bool = Field(
        default=...,
        description="Whether user has superuser privileges.",
        examples=[False],
    )
    created_at: datetime = Field(
        default=...,
        description="Timestamp when the user was created.",
        examples=["2025-01-01T12:34:56Z"],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Timestamp when the user was last updated.",
        examples=["2025-01-01T12:35:10Z"],
    )


__all__: list[str] = ["ActivateAccountResponse"]
