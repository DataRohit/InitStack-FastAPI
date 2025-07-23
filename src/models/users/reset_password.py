# Standard Library Imports
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field


# User Reset Password Request Model
class UserResetPasswordRequest(BaseModel):
    """
    User Reset Password Request Model

    This Model Defines the Structure of User Reset Password Data.

    Attributes:
        identifier (str): Unique Username or Email
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Authentication Fields
    identifier: str = Field(
        ...,
        example="johndoe/john_doe@example.com",
        description="Unique Username or Email",
    )


# Exports
__all__: list[str] = ["UserResetPasswordRequest"]
