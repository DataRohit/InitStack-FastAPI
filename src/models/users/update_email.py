# Standard Library Imports
from typing import Any, ClassVar

# Third-Party Imports
from pydantic import BaseModel, EmailStr, Field, field_validator


# User Update Email Request Model
class UserUpdateEmailRequest(BaseModel):
    """
    User Update Email Request Model

    This Model Defines the Structure of the Request Body for Initiating a User Email Update.

    Attributes:
        email (EmailStr): The New Email Address to Update To.
        confirm_email (EmailStr): Confirmation of the New Email Address.
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Email Fields
    email: EmailStr = Field(
        ...,
        example="new_email@example.com",
        description="The New Email Address to Update To",
    )
    confirm_email: EmailStr = Field(
        ...,
        example="new_email@example.com",
        description="Confirmation of the New Email Address",
    )

    # Email Match Validation
    @field_validator("confirm_email")
    @classmethod
    def validate_email_match(cls, value: str, values: Any) -> str:
        """
        Validate Email Match

        Ensures Email and Confirm Email Match

        Args:
            value (str): Confirm Email to Validate
            values (Any): Other Field Values

        Returns:
            str: Validated Confirm Email

        Raises:
            ValueError: If Emails Don't Match
        """

        # If Emails Don't Match
        if "email" in values.data and value != values.data["email"]:
            # Raise ValueError
            raise ValueError({"reason": "Emails Do Not Match"})

        # Return Validated Confirm Email
        return value
