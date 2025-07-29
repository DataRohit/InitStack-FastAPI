# Standard Library Imports
import re
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field, field_validator


# User Update Username Confirm Request Model
class UserUpdateUsernameConfirmRequest(BaseModel):
    """
    User Update Username Confirm Request Model

    This Model Defines the Structure of User Update Username Confirm Data.

    Attributes:
        username (str): Unique Username with Specific Formatting
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Authentication Fields
    username: str = Field(
        ...,
        example="john_doe",
        description="Unique Username (Lowercase, Alphanumeric with @-_)",
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
__all__: list[str] = ["UserUpdateUsernameConfirmRequest"]
