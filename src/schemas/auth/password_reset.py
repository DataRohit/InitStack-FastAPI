import re

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class ForgotPasswordRequest(BaseModel):
    """Forgot Password Request Schema.

    Inherits:
        BaseModel

    Attributes:
        username (str | None): Username.
        email (str | None): Email address.

    Properties:
        None

    Methods:
        validate_identifier: Validate that exactly one identifier is provided.
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

    @model_validator(mode="after")
    def validate_identifier(self) -> ForgotPasswordRequest:
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


class ResetPasswordRequest(BaseModel):
    """Reset Password Request Schema.

    Inherits:
        BaseModel

    Attributes:
        password (str): New password.
        re_password (str): Password confirmation.

    Properties:
        None

    Methods:
        validate_passwords_match: Validate password and re_password match.
    """

    model_config: ConfigDict = ConfigDict()

    password: str = Field(
        default=...,
        description="New password.",
        min_length=1,
    )
    re_password: str = Field(
        default=...,
        description="Password confirmation.",
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_passwords_match(self) -> ResetPasswordRequest:
        if self.password != self.re_password:
            msg = "Passwords do not match"
            raise ValueError(msg)
        return self


class MessageResponse(BaseModel):
    """Message Response Schema.

    Inherits:
        BaseModel

    Attributes:
        message (str): Response message.

    Properties:
        None

    Methods:
        None
    """

    model_config: ConfigDict = ConfigDict()

    message: str = Field(
        default=...,
        description="Response message.",
        examples=["If the account exists, a reset link has been sent"],
    )


__all__: list[str] = [
    "ForgotPasswordRequest",
    "MessageResponse",
    "ResetPasswordRequest",
]
