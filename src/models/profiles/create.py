# Standard Library Imports
import datetime
from typing import ClassVar

# Third-Party Imports
from pydantic import BaseModel, Field


# Profile Create Request Model
class ProfileCreateRequest(BaseModel):
    """
    Profile Create Request Model

    This Model Defines the Structure of Profile Creation Data.

    Attributes:
        bio (str | None): User Biography
        phone_number (str | None): Valid Phone Number
        date_of_birth (datetime.date | None): User's Birth Date
        gender (str | None): User's Gender
        country (str | None): User's Country
        city (str | None): User's City
        timezone (str | None): User's Timezone
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Personal Information
    bio: str | None = Field(
        default=None,
        example="Software developer and open source enthusiast",
        description="User Biography",
        max_length=500,
    )
    phone_number: str | None = Field(
        default=None,
        example="+1234567890",
        description="Valid Phone Number",
    )
    date_of_birth: datetime.date | None = Field(
        default=None,
        example="1990-01-01",
        description="User's Birth Date",
    )
    gender: str | None = Field(
        default=None,
        example="male",
        description="User's Gender",
    )

    # Location Information
    country: str | None = Field(
        default=None,
        example="United States",
        description="User's Country",
    )
    city: str | None = Field(
        default=None,
        example="New York",
        description="User's City",
    )
    timezone: str | None = Field(
        default=None,
        example="America/New_York",
        description="User's Timezone",
    )


# Exports
__all__: list[str] = ["ProfileCreateRequest"]
