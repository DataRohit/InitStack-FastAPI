# Standard Library Imports
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field


# User Register Request Model
class UserRegisterRequest(BaseModel):
    """
    User Register Request Model

    This Model Defines the Structure of User Registration Data.

    Attributes:
        username (str): Unique Username with Specific Formatting
        email (str): Valid Email Address
        password (str): Plain Text Password
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


# Exports
__all__: list[str] = ["UserRegisterRequest"]
