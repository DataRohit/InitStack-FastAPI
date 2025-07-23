# Standard Library Imports
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field

from src.models.users.base import UserResponse


# User Login Request Model
class UserLoginRequest(BaseModel):
    """
    User Login Request Model

    This Model Defines the Structure of User Login Data.

    Attributes:
        identifier (str): Unique Username or Email
        password (str): Plain Text Password
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Authentication Fields
    identifier: str = Field(
        ...,
        example="johndoe/john_doe@example.com",
        description="Unique Username or Email",
    )
    password: str = Field(
        ...,
        example="SecurePassword@123",
        description="Plain Text Password",
    )


# User Login Response
class UserLoginResponse(BaseModel):
    """
    User Login Response Model

    This Model Defines the Structure of User Login Response Data.

    Attributes:
        user (UserResponse): User Data
        access_token (UserLoginResponseAccessToken): Access Token Data
        refresh_token (UserLoginResponseRefreshToken): Refresh Token Data
    """

    # User Login Response Access Token Model
    class UserLoginResponseAccessToken(BaseModel):
        """
        User Login Response Access Token Model

        This Model Defines the Structure of User Login Response Access Token Data.

        Attributes:
            token (str): JWT Access Token
            type (str): Token Type
            expires_in (int): Token Expiry in Seconds
        """

        # Model Configuration
        model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

        # Authentication Fields
        token: str = Field(
            ...,
            example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            description="JWT Access Token",
        )
        type: str = Field(
            ...,
            example="bearer",
            description="Token Type",
        )
        expires_in: int = Field(
            ...,
            example=3600,
            description="Token Expiry in Seconds",
        )

    # User Login Response Refresh Token Model
    class UserLoginResponseRefreshToken(BaseModel):
        """
        User Login Response Refresh Token Model

        This Model Defines the Structure of User Login Response Refresh Token Data.

        Attributes:
            token (str): JWT Refresh Token
            expires_in (int): Token Expiry in Seconds
        """

        # Model Configuration
        model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

        # Authentication Fields
        token: str = Field(
            ...,
            example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            description="JWT Refresh Token",
        )
        expires_in: int = Field(
            ...,
            example=86400,
            description="Token Expiry in Seconds",
        )

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # User Data
    user: UserResponse = Field(
        ...,
        description="User Data",
    )

    # Authentication Fields
    access_token: UserLoginResponseAccessToken = Field(
        ...,
        description="JWT Access Token",
    )
    refresh_token: UserLoginResponseRefreshToken = Field(
        ...,
        description="JWT Refresh Token",
    )
