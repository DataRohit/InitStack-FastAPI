# Standard Library Imports
import re
from typing import Any, ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field, field_validator


# User Update Username Confirm Request Model
class UserUpdateUsernameConfirmRequest(BaseModel):
    """
    User Update Username Confirm Request Model

    This Model Defines the Structure of the Request Body for Confirming a User Username Update.

    Attributes:
        username (str): The New Username to Update To.
        confirm_username (str): Confirmation of the New Username.
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Username Fields
    username: str = Field(
        ...,
        example="new_username",
        description="The New Username to Update To",
    )
    confirm_username: str = Field(
        ...,
        example="new_username",
        description="Confirmation of the New Username",
    )

    # Username Match Validation
    @field_validator("confirm_username")
    @classmethod
    def validate_username_match(cls, value: str, values: Any) -> str:
        """
        Validate Username Match

        Ensures Username and Confirm Username Match

        Args:
            value (str): Confirm Username to Validate
            values (Any): Other Field Values

        Returns:
            str: Validated Confirm Username

        Raises:
            ValueError: If Usernames Don't Match
        """

        # If Usernames Don't Match
        if "username" in values.data and value != values.data["username"]:
            # Raise ValueError
            raise ValueError({"reason": "Usernames Do Not Match"})

        # Return Validated Confirm Username
        return value

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
