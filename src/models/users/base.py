# Standard Library Imports
import datetime
import re

# Third-Party Imports
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError, VerifyMismatchError
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator

# Initialize Password Hasher
ph = PasswordHasher()


# User Model
class User(BaseModel):
    """
    User Model

    This Model Defines the Structure of User Data in the System.

    Attributes:
        id (ObjectId): Unique User Identifier
        username (str): Unique Username with Specific Formatting
        first_name (str): User's First Name
        last_name (str): User's Last Name
        email (str): Valid Email Address
        password (str): Hashed Password
        is_active (bool): Account Activation Status
        is_staff (bool): Staff Access Status
        is_superuser (bool): Admin Access Status
        date_joined (datetime): Account Creation Timestamp
        last_login (datetime): Last Login Timestamp
        updated_at (datetime): Last Update Timestamp
    """

    # User Identifier
    id: ObjectId = Field(
        default_factory=ObjectId,
        example="507f1f77bcf86cd799439011",
        description="Unique User Identifier",
    )

    # Authentication Fields
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        example="john_doe",
        description="Unique Username (lowercase, alphanumeric with @-_)",
    )
    email: EmailStr = Field(
        ...,
        example="john_doe@example.com",
        description="Valid Email Address",
    )
    password: str = Field(
        ...,
        example="$argon2id$v=19$m=65536,t=3,p=4$MIIRqgvgQbgj220jfp0MPA$YfwJSVjtjSU0zzV/P3S9nnQ/USre2wvJMjfCIjrTQbg",
        description="Hashed Password",
    )

    # Personal Information
    first_name: str = Field(
        ...,
        min_length=3,
        max_length=30,
        example="John",
        description="User's First Name (letters only)",
    )
    last_name: str = Field(
        ...,
        min_length=3,
        max_length=30,
        example="Doe",
        description="User's Last Name (letters only)",
    )

    # Status Flags
    is_active: bool = Field(
        default=False,
        example=False,
        description="Account Activation Status",
    )
    is_staff: bool = Field(
        default=False,
        example=False,
        description="Staff Access Status",
    )
    is_superuser: bool = Field(
        default=False,
        example=False,
        description="Admin Access Status",
    )

    # Timestamps
    date_joined: datetime = Field(
        default_factory=datetime.now(datetime.UTC),
        example="2025-07-21T08:56:30.123456",
        description="Account Creation Timestamp",
    )
    last_login: datetime | None = Field(
        default=None,
        example="2025-07-21T08:56:30.123456",
        description="Last Login Timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now(datetime.UTC),
        example="2025-07-21T08:56:30.123456",
        description="Last Update Timestamp",
    )

    # Password Management
    def _validate_password_complexity(self, password: str) -> list[str]:
        """
        Validate Password Complexity Requirements

        Args:
            password (str): Password to Validate

        Returns:
            list[str]: List of Error Messages
        """

        # List to Store Errors
        errors = []

        # Define Complexity Checks
        checks = [
            (r"[a-z]", "Password Must Contain at Least One Lowercase Letter"),
            (r"[A-Z]", "Password Must Contain at Least One Uppercase Letter"),
            (r"[0-9]", "Password Must Contain at Least One Number"),
            (r"[^A-Za-z0-9]", "Password Must Contain at Least One Special Character"),
        ]

        # Traverse Checks
        for pattern, message in checks:
            # If Pattern is Not Found
            if not re.search(pattern, password):
                # Append Error Message
                errors.append(message)

        # Return Errors
        return errors

    # Check for Personal Info in Password
    def _check_personal_info_in_password(self, password: str) -> list[str]:
        """
        Check for Personal Info in Password

        Args:
            password (str): Password to Check

        Returns:
            list[str]: List of Error Messages
        """

        # List to Store Errors
        errors = []

        # User Info
        user_info = {
            self.username: "Username",
            self.email.split("@")[0]: "Email",
            self.first_name.lower(): "First Name",
            self.last_name.lower(): "Last Name",
        }

        # Traverse User Info
        for info, label in user_info.items():
            # If Info is Not Empty and is in Password
            if info and info.lower() in password.lower():
                # Append Error Message
                errors.append(f"Password Cannot Contain Your {label}")

        # Return Errors
        return errors

    # Set Password
    def set_password(self, password: str) -> None:
        """
        Hash and Set User Password

        Uses Argon2 for Secure Password Hashing
        Validates Password Meets Complexity Requirements:
        - At Least 1 Lowercase Letter
        - At Least 1 Uppercase Letter
        - At Least 1 Number
        - At Least 1 Special Character
        - Not Containing Username/Email/Name Parts

        Args:
            password (str): Plain Text Password to Hash

        Raises:
            ValueError: If Password Doesn't Meet Requirements
            HashingError: If Password Hashing Fails
        """

        # List to Store Errors
        errors = []

        # Validate Password Complexity
        errors.extend(self._validate_password_complexity(password))

        # Check for Personal Info in Password
        errors.extend(self._check_personal_info_in_password(password))

        # If Errors are Found
        if errors:
            # Raise ValueError
            raise ValueError("Password Validation Failed: " + "; ".join(errors))

        try:
            # Hash Password
            self.password = ph.hash(password)

        except HashingError as e:
            # Set Error Message
            msg = "Failed to Hash Password"

            # Raise HashingError
            raise HashingError(msg) from e

    # Verify Password
    def verify_password(self, password: str) -> bool:
        """
        Verify User Password

        Compares Input Password with Stored Hash

        Args:
            password (str): Plain Text Password to Verify

        Returns:
            bool: True if Password Matches, False Otherwise

        Raises:
            VerificationError: If Password Verification Fails
        """

        try:
            # Verify Password
            return ph.verify(self.password, password)

        except (VerifyMismatchError, VerificationError, InvalidHashError):
            # Return False
            return False

    # Username Validation
    @field_validator("username")
    def validate_username(self, value: str) -> str:
        """
        Validate Username Format

        Ensures Username Contains Only:
        - Lowercase Letters
        - Numbers
        - @, -, _ Special Characters

        Args:
            value (str): Username to Validate

        Returns:
            str: Validated Username in Lowercase

        Raises:
            ValueError: If Username Contains Invalid Characters
        """

        # If Username Contains Invalid Characters
        if not re.match(r"^[a-z0-9@_-]+$", value):
            # Set Error Message
            msg = "Username May Only Contain Lowercase Letters, Numbers, @, -, _"

            # Raise ValueError
            raise ValueError(msg)

        # Return Validated Username in Lowercase
        return value.lower()

    # Name Validation
    @field_validator("first_name", "last_name")
    def validate_name(self, value: str) -> str:
        """
        Validate Name Format

        Ensures Name Contains Only Letters

        Args:
            value (str): Name to Validate

        Returns:
            str: Validated Name

        Raises:
            ValueError: If Name Contains Invalid Characters
        """

        # If Name Contains Invalid Characters
        if not value.isalpha():
            # Set Error Message
            msg = "Name May Only Contain Letters"

            # Raise ValueError
            raise ValueError(msg)

        # Return Validated Name
        return value


# Exports
__all__: list[str] = ["User"]
