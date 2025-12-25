# ruff: noqa: TC003

import re
import uuid

from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import validates

from src.models.base import TimestampedModel


class User(TimestampedModel):
    """User Model For Application Users.

    Inherits:
        TimestampedModel

    Attributes:
        id (Uuid): Primary key UUID (inherited).
        username (str): Unique username (lowercase, alphanumeric with underscores).
        email (str): Unique email address (lowercase).
        first_name (str): User's first name (title case, text only).
        last_name (str): User's last name (title case, text only).
        is_active (bool): Whether user account is active.
        is_admin (bool): Whether user has admin privileges.
        is_superuser (bool): Whether user has superuser privileges.
        created_at (datetime): Timestamp when user was created (inherited).
        updated_at (datetime): Timestamp when user was last updated (inherited).

    Properties:
        None

    Methods:
        validate_username: Validate username format.
        validate_email: Validate email format.
        validate_first_name: Validate first name format.
        validate_last_name: Validate last name format.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(length=50),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(length=255),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    __table_args__: tuple[CheckConstraint, CheckConstraint, CheckConstraint, CheckConstraint, CheckConstraint] = (
        CheckConstraint(
            "username ~ '^[a-z0-9][a-z0-9_]*$'",
            name="username_format_check",
        ),
        CheckConstraint(
            "username !~ '^_'",
            name="username_no_leading_underscore_check",
        ),
        CheckConstraint(
            "email ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$'",
            name="email_format_check",
        ),
        CheckConstraint(
            "first_name ~ '^[A-Z][a-z]*$'",
            name="first_name_format_check",
        ),
        CheckConstraint(
            "last_name ~ '^[A-Z][a-z]*$'",
            name="last_name_format_check",
        ),
    )

    @validates("username")
    def validate_username(self, key: str, value: str) -> str:
        """Validate Username Format.

        Arguments:
            key (str): Field name.
            value (str): Username value.

        Returns:
            str: Validated and normalized username.

        Raises:
            ValueError: If username format is invalid.
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

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        """Validate Email Format.

        Arguments:
            key (str): Field name.
            value (str): Email value.

        Returns:
            str: Validated and normalized email.

        Raises:
            ValueError: If email format is invalid.
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

    @validates("first_name")
    def validate_first_name(self, key: str, value: str) -> str:
        """Validate First Name Format.

        Arguments:
            key (str): Field name.
            value (str): First name value.

        Returns:
            str: Validated and normalized first name.

        Raises:
            ValueError: If first name format is invalid.
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

    @validates("last_name")
    def validate_last_name(self, key: str, value: str) -> str:
        """Validate Last Name Format.

        Arguments:
            key (str): Field name.
            value (str): Last name value.

        Returns:
            str: Validated and normalized last name.

        Raises:
            ValueError: If last name format is invalid.
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

    def __repr__(self) -> str:
        """String Representation Of User.

        Arguments:
            None

        Returns:
            str: String representation.

        Raises:
            None
        """

        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class OAuthAccount(TimestampedModel):
    """OAuth Account Model For Linking External Provider Accounts.

    Inherits:
        TimestampedModel

    Attributes:
        id (Uuid): Primary key UUID (inherited).
        user_id (Uuid): Foreign key to users.id.
        provider (str): OAuth provider name.
        provider_account_id (str): Unique identifier for the account within the provider.
        email (str | None): Optional email returned by provider.
        created_at (datetime): Timestamp when record was created (inherited).
        updated_at (datetime): Timestamp when record was last updated (inherited).

    Properties:
        None

    Methods:
        validate_email: Validate email format when provided.
    """

    __tablename__ = "oauth_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(column="users.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False,
        index=True,
    )

    provider_account_id: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(length=255),
        nullable=True,
    )

    __table_args__: tuple[UniqueConstraint] = (
        UniqueConstraint(
            "provider",
            "provider_account_id",
            name="uq_oauth_accounts_provider_provider_account_id",
        ),
    )

    @validates("email")
    def validate_email(self, key: str, value: str | None) -> str | None:
        """Validate Email Format When Provided.

        Arguments:
            key (str): Field name.
            value (str | None): Email value.

        Returns:
            str | None: Validated and normalized email.

        Raises:
            ValueError: If email format is invalid.
        """

        if value is None:
            return None

        value: str = value.lower()

        email_pattern: str = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
        if not re.match(pattern=email_pattern, string=value):
            msg = "Invalid email format"
            raise ValueError(msg)

        if len(value) > 255:  # noqa: PLR2004
            msg = "Email cannot exceed 255 characters"
            raise ValueError(msg)

        return value

    def __repr__(self) -> str:
        """String Representation Of OAuthAccount.

        Arguments:
            None

        Returns:
            str: String representation.

        Raises:
            None
        """

        return (
            f"<OAuthAccount(id={self.id}, user_id={self.user_id}, provider={self.provider}, "
            f"provider_account_id={self.provider_account_id})>"
        )


__all__: list[str] = ["OAuthAccount", "User"]
