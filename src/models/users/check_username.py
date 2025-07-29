# Standard Library Imports
import re
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field, field_validator


# User Check Username Request Model
class UserCheckUsernameRequest(BaseModel):
    """
    User Check Username Request Model

    This Model Defines the Structure for Checking Username Availability.

    Attributes:
        username (str): Username to Check for Availability
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Username Field
    username: str = Field(
        ...,
        example="john_doe",
        description="Username to Check for Availability (Lowercase, Alphanumeric with @-_)",
    )

    # Username Validation
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
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
        if not re.match(pattern=r"^[a-z0-9@\-_]{8,}$", string=value):
            # Raise ValueError
            raise ValueError({"reason": "Username Must Be 8+ Characters, Using Lowercase Letters, Numbers, @, -, _"})

        # Return Validated Username in Lowercase
        return value.lower()


# Exports
__all__: list[str] = ["UserCheckUsernameRequest"]
