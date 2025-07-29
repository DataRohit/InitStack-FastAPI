# Standard Library Imports
from typing import Any, ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field, field_validator


# User Reset Password Confirm Request Model
class UserResetPasswordConfirmRequest(BaseModel):
    """
    User Reset Password Confirm Request Model

    This Model Defines the Structure of User Reset Password Confirm Data.

    Attributes:
        password (str): Plain Text Password
        confirm_password (str): Confirm Plain Text Password
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Authentication Fields
    password: str = Field(
        ...,
        example="SecurePassword@123",
        description="Plain Text Password",
    )
    confirm_password: str = Field(
        ...,
        example="SecurePassword@123",
        description="Confirm Plain Text Password",
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
__all__: list[str] = ["UserResetPasswordConfirmRequest"]
