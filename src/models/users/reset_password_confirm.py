# Standard Library Imports
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field, model_validator


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

    # Model Validators
    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserResetPasswordConfirmRequest":
        """
        Check Passwords Match

        Ensures Passwords Match

        Returns:
            UserResetPasswordConfirmRequest: UserResetPasswordConfirmRequest

        Raises:
            ValueError: If Passwords Do Not Match
        """

        # If Passwords Do Not Match
        if self.password != self.confirm_password:
            # Set Error Message
            msg = "Passwords Do Not Match"

            # Raise ValueError
            raise ValueError(msg)

        # Return UserResetPasswordConfirmRequest
        return self


# Exports
__all__: list[str] = ["UserResetPasswordConfirmRequest"]
