# Standard Library Imports
from typing import Any, ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field, field_validator


# User Register Request Model
class UserRegisterRequest(BaseModel):
    """
    User Register Request Model

    This Model Defines the Structure of User Registration Data.

    Attributes:
        username (str): Unique Username with Specific Formatting
        email (str): Valid Email Address
        password (str): Plain Text Password
        confirm_password (str): Password Confirmation
        first_name (str): User's First Name
        last_name (str): User's Last Name
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Authentication Fields
    username: str = Field(
        ...,
        example="john_doe",
        description="Unique Username (Lowercase, Alphanumeric with @-_)",
    )
    email: str = Field(
        ...,
        example="john_doe@example.com",
        description="Valid Email Address",
    )
    password: str = Field(
        ...,
        example="SecurePassword@123",
        description="Plain Text Password",
    )
    confirm_password: str = Field(
        ...,
        example="SecurePassword@123",
        description="Password Confirmation",
    )

    # Personal Information
    first_name: str = Field(
        ...,
        example="John",
        description="User's First Name (Alphabetic Characters Only)",
    )
    last_name: str = Field(
        ...,
        example="Doe",
        description="User's Last Name (Alphabetic Characters Only)",
    )

    # Password Match Validation
    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, value: str, values: Any) -> str:
        """
        Validate Password Match

        Ensures Password and Confirm Password Match

        Args:
            value (str): Confirm Password to Validate
            values (Any): Other Field Values

        Returns:
            str: Validated Confirm Password

        Raises:
            ValueError: If Passwords Don't Match
        """

        # If Passwords Don't Match
        if "password" in values.data and value != values.data["password"]:
            # Raise ValueError
            raise ValueError({"reason": "Passwords Do Not Match"})

        # Return Validated Confirm Password
        return value


# Exports
__all__: list[str] = ["UserRegisterRequest"]
