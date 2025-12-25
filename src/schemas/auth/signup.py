import re
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class SignUpRequest(BaseModel):
    """Sign Up Request Schema.

    Inherits:
        BaseModel

    Attributes:
        username (str): Username (lowercase, alphanumeric with underscores).
        email (str): Email address.
        password (str): Plain text password.
        re_password (str): Password confirmation.
        first_name (str): User's first name.
        last_name (str): User's last name.

    Properties:
        None

    Methods:
        validate_and_normalize: Validate and normalize inputs.
    """

    model_config: ConfigDict = ConfigDict()

    username: str = Field(
        default=...,
        description="Unique username (lowercase, alphanumeric with underscores).",
        examples=["john_doe", "user123"],
        max_length=50,
    )
    email: str = Field(
        default=...,
        description="Unique email address.",
        examples=["user@example.com"],
        max_length=255,
    )
    password: str = Field(
        default=...,
        description="Plain text password.",
        min_length=1,
    )
    re_password: str = Field(
        default=...,
        description="Password confirmation.",
        min_length=1,
    )
    first_name: str = Field(
        default=...,
        description="User's first name.",
        examples=["John"],
        max_length=50,
    )
    last_name: str = Field(
        default=...,
        description="User's last name.",
        examples=["Doe"],
        max_length=50,
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Validate And Normalize Username.

        Arguments:
            cls (type[SignUpRequest]): Model class.
            value (str): Raw username input.

        Returns:
            str: Validated and normalized username (lowercase).

        Raises:
            ValueError: If the username is empty or fails format/length constraints.
        """

        if not value:
            msg = "Username cannot be empty"
            raise ValueError(msg)

        value: str = value.lower()

        if value.startswith("_"):
            msg = "Username cannot start with underscore"
            raise ValueError(msg)

        if not re.match(pattern=r"^[a-z0-9][a-z0-9_]*$", string=value):
            msg = "Username must be alphanumeric with underscores, starting with letter or number"
            raise ValueError(msg)

        if len(value) > 50:  # noqa: PLR2004
            msg = "Username cannot exceed 50 characters"
            raise ValueError(msg)

        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate And Normalize Email.

        Arguments:
            cls (type[SignUpRequest]): Model class.
            value (str): Raw email input.

        Returns:
            str: Validated and normalized email (lowercase).

        Raises:
            ValueError: If the email is empty, invalid format, or exceeds length constraints.
        """

        if not value:
            msg = "Email cannot be empty"
            raise ValueError(msg)

        value: str = value.lower()
        email_pattern: str = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
        if not re.match(pattern=email_pattern, string=value):
            msg = "Invalid email format"
            raise ValueError(msg)

        if len(value) > 255:  # noqa: PLR2004
            msg = "Email cannot exceed 255 characters"
            raise ValueError(msg)

        return value

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        """Validate And Normalize First Name.

        Arguments:
            cls (type[SignUpRequest]): Model class.
            value (str): Raw first name input.

        Returns:
            str: Validated and normalized first name (title case).

        Raises:
            ValueError: If the first name is empty or fails format/length constraints.
        """

        if not value:
            msg = "First name cannot be empty"
            raise ValueError(msg)

        value: str = value.strip().title()
        if not re.match(pattern=r"^[A-Z][a-z]*$", string=value):
            msg = "First name must contain only letters and be a single word"
            raise ValueError(msg)

        if len(value) > 50:  # noqa: PLR2004
            msg = "First name cannot exceed 50 characters"
            raise ValueError(msg)

        return value

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value: str) -> str:
        """Validate And Normalize Last Name.

        Arguments:
            cls (type[SignUpRequest]): Model class.
            value (str): Raw last name input.

        Returns:
            str: Validated and normalized last name (title case).

        Raises:
            ValueError: If the last name is empty or fails format/length constraints.
        """

        if not value:
            msg = "Last name cannot be empty"
            raise ValueError(msg)

        value: str = value.strip().title()
        if not re.match(pattern=r"^[A-Z][a-z]*$", string=value):
            msg = "Last name must contain only letters and be a single word"
            raise ValueError(msg)

        if len(value) > 50:  # noqa: PLR2004
            msg = "Last name cannot exceed 50 characters"
            raise ValueError(msg)

        return value

    @model_validator(mode="after")
    def validate_passwords_match(self) -> SignUpRequest:
        """Validate Password And Confirmation Match.

        Arguments:
            self (SignUpRequest): Validated request instance.

        Returns:
            SignUpRequest: The same instance if passwords match.

        Raises:
            ValueError: If password and re_password do not match.
        """

        if self.password != self.re_password:
            msg = "Passwords do not match"
            raise ValueError(msg)

        return self


class SignUpResponse(BaseModel):
    """Sign Up Response Schema.

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
        examples=[False],
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
        examples=["2025-01-01T12:34:56Z"],
    )


__all__: list[str] = ["SignUpRequest", "SignUpResponse"]
