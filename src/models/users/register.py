# Standard Library Imports
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field

# Local Imports
from src.models.users.base import UserResponse


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


# User Register Response Model
class UserRegisterResponse(BaseModel):
    """
    User Register Response Model

    This Model Defines the Structure of User Registration Response Data.

    Attributes:
        user (UserResponse): Registered User Instance (without sensitive fields)
        activation_token (str): Account Activation Token
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # User Data
    user: UserResponse = Field(
        ...,
        description="Registered User Data (without sensitive fields)",
    )

    # Activation Token
    activation_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjVkY2Y4YzYwYjI0ZTAwMTFlYjQ4YjQ5IiwiaWF0IjoxNzE4ODQ1NjAwLCJleHAiOjE3MTg5MzIwMDB9.1q3X2Q4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0",
        description="JWT Token for Account Activation",
    )


# Exports
__all__: list[str] = ["UserRegisterRequest", "UserRegisterResponse"]
