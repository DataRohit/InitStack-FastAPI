import re
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class LoginRequest(BaseModel):
    """Login Request Schema.

    Inherits:
        BaseModel

    Attributes:
        username (str | None): Username.
        email (str | None): Email address.
        password (str): Plain text password.

    Properties:
        None

    Methods:
        validate_login_identifier: Validate that exactly one identifier is provided.
    """

    model_config: ConfigDict = ConfigDict()

    username: str | None = Field(
        default=None,
        description="Username.",
        examples=["john_doe"],
        max_length=50,
    )
    email: str | None = Field(
        default=None,
        description="Email address.",
        examples=["user@example.com"],
        max_length=255,
    )
    password: str = Field(
        default=...,
        description="Plain text password.",
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_login_identifier(self) -> LoginRequest:
        """Validate Login Identifier.

        Arguments:
            self (LoginRequest): Validated request instance.

        Returns:
            LoginRequest: The same instance if identifier is valid.

        Raises:
            ValueError: If username/email are missing, both provided, or invalid.
        """

        username: str | None = self.username.strip().lower() if isinstance(self.username, str) else None
        email: str | None = self.email.strip().lower() if isinstance(self.email, str) else None

        if bool(username) == bool(email):
            msg = "Provide exactly one of username or email"
            raise ValueError(msg)

        if username is not None:
            if username.startswith("_"):
                msg = "Username cannot start with underscore"
                raise ValueError(msg)

            if not re.match(pattern=r"^[a-z0-9][a-z0-9_]*$", string=username):
                msg = "Username must be alphanumeric with underscores, starting with letter or number"
                raise ValueError(msg)

            if len(username) > 50:  # noqa: PLR2004
                msg = "Username cannot exceed 50 characters"
                raise ValueError(msg)

        if email is not None:
            email_pattern: str = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
            if not re.match(pattern=email_pattern, string=email):
                msg = "Invalid email format"
                raise ValueError(msg)

            if len(email) > 255:  # noqa: PLR2004
                msg = "Email cannot exceed 255 characters"
                raise ValueError(msg)

        self.username: str | None = username
        self.email: str | None = email

        return self


class LoginResponse(BaseModel):
    """Login Response Schema.

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
        access_token (str): Access token.
        refresh_token (str): Refresh token.

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
    access_token: str = Field(
        default=...,
        description="JWT access token.",
    )
    refresh_token: str = Field(
        default=...,
        description="JWT refresh token.",
    )


__all__: list[str] = ["LoginRequest", "LoginResponse"]
