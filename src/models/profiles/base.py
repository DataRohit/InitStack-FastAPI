# Standard Library Imports
import datetime
import re
from typing import Any, ClassVar

# Third-Party Imports
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator

# Local Imports
from config.settings import settings


# Profile Model
class Profile(BaseModel):
    """
    Profile Model

    This Model Defines the Structure of User Profile Data in the System.

    Attributes:
        id (str | None): Unique Profile Identifier
        user_id (str): Reference to User Model
        bio (str | None): User Biography
        phone_number (str | None): Valid Phone Number
        date_of_birth (datetime.date | None): User's Birth Date
        gender (str | None): User's Gender
        avatar_url (str | None): URL to User's Avatar
        country (str | None): User's Country
        city (str | None): User's City
        timezone (str | None): User's Timezone
        created_at (datetime.datetime): Profile Creation Timestamp
        updated_at (datetime.datetime): Last Update Timestamp
    """

    # Model Configuration
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "validate_by_name": True,
        "extra": "forbid",
    }

    # Profile Identifier
    id: str | None = Field(
        default_factory=lambda: str(ObjectId()),
        alias="_id",
        example="507f1f77bcf86cd799439011",
        description="Unique Profile Identifier",
    )

    # User Reference
    user_id: str = Field(
        ...,
        example="507f1f77bcf86cd799439011",
        description="Reference to User Model",
    )

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

    # Avatar
    avatar_url: str = Field(
        default_factory=lambda: f"{settings.DICEBEAR_URL}?seed=admin&accessories=&eyebrows=default%2CdefaultNatural&eyes=default%2Chappy%2Cwink&mouth=default%2Csmile",  # noqa: E501
        example=f"{settings.DICEBEAR_URL}?seed=admin&accessories=&eyebrows=default%2CdefaultNatural&eyes=default%2Chappy%2Cwink&mouth=default%2Csmile",
        description="URL of User's Avatar Image (Generated from Dicebear)",
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

    # Timestamps
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC),
        example="2025-07-21T08:56:30.123000+00:00",
        description="Profile Creation Timestamp",
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC),
        example="2025-07-21T09:30:30.123000+00:00",
        description="Last Update Timestamp",
    )

    # User ID Validation
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        """
        Validate User ID Format

        Ensures User ID is a Valid MongoDB ObjectId

        Args:
            value (str): User ID to Validate

        Returns:
            str: Validated User ID

        Raises:
            ValueError: If User ID is Not a Valid ObjectId
        """

        # If Value is Not a Valid ObjectId
        if not ObjectId.is_valid(value):
            # Raise ValueError
            raise ValueError(
                {"reason": "User ID Must Be a Valid MongoDB ObjectId"},
            )

        # Return Validated User ID
        return value

    # Phone Number Validation
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        """
        Validate Phone Number Format

        Args:
            value (str | None): Phone Number to Validate

        Returns:
            str | None: Validated Phone Number

        Raises:
            ValueError: If Phone Number is Invalid
        """

        # If Phone Number is None
        if value is None:
            # Return None
            return None

        # Remove All Non-Digit Characters
        digits = re.sub(r"\D", "", value)

        # If Phone Number is Not 7-15 Digits Long
        if not 7 <= len(digits) <= 15:  # noqa: PLR2004
            # Raise ValueError
            raise ValueError({"reason": "Phone Number Must Be 7-15 Digits Long"})

        # Return Validated Phone Number
        return value

    # Date of Birth Validation
    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: datetime.date | None) -> datetime.date | None:
        """
        Validate Date of Birth

        Args:
            value (datetime.date | None): Date to Validate

        Returns:
            datetime.date | None: Validated Date

        Raises:
            ValueError: If Date is in the Future or Too Far in the Past
        """

        # If Date is None
        if value is None:
            # Return None
            return None

        # Get Today's Date
        today = datetime.datetime.now(tz=datetime.UTC).date()

        # Get Minimum Age Date
        min_age_date = today.replace(year=today.year - 18)

        # If Date is in the Future
        if value > today:
            # Raise ValueError
            raise ValueError({"reason": "Date of Birth Cannot Be in the Future"})

        # If Date is More Than 18 Years Ago
        if value > min_age_date:
            # Raise ValueError
            raise ValueError({"reason": "Date of Birth Cannot Be More Than 18 Years Ago"})

        # Return Validated Date
        return value

    # Gender Validation
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        """
        Validate Gender

        Args:
            value (str | None): Gender to Validate

        Returns:
            str | None: Validated Gender

        Raises:
            ValueError: If Gender is Not One of the Allowed Values
        """

        # If Gender is None
        if value is None:
            # Return None
            return None

        # List of Allowed Genders
        allowed_genders = ["male", "female", "non-binary", "other"]

        # If Gender is Not One of the Allowed Values
        if value.lower() not in allowed_genders:
            # Raise ValueError
            raise ValueError({"reason": f"Gender Must Be One of: {', '.join(allowed_genders)}"})

        # Return Validated Gender
        return value.lower()

    # Model Dump
    def model_dump(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> dict:
        """
        Model Dump

        This Method Overrides the Default Model Dump Method to Convert Date Objects to DateTime

        Args:
            *args (tuple[Any, ...]): Positional Arguments
            **kwargs (dict[str, Any]): Keyword Arguments

        Returns:
            dict: Model Dump Data
        """

        # Get Model Dump Data
        data = super().model_dump(*args, **kwargs)

        # Convert DateTime Objects to ISO Format
        for field in ["date_of_birth"]:
            # Get Field Value
            value = getattr(self, field)

            # If Field Value is a Date Object
            if isinstance(value, datetime.date):
                # Convert to DateTime Object
                data[field] = datetime.datetime.combine(value, datetime.time.min)

        # Return Model Dump Data
        return data


# Profile Response Model
class ProfileResponse(BaseModel):
    """
    Profile Response Model

    This Model Defines the Structure of Profile Data Returned in API Responses.
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Identification Fields
    id: str = Field(
        ...,
        example="507f1f77bcf86cd799439011",
        description="Unique Profile Identifier",
    )
    user_id: str = Field(
        ...,
        example="507f1f77bcf86cd799439011",
        description="Reference to User Model",
    )

    # Personal Information
    bio: str | None = Field(
        example="Software developer and open source enthusiast",
        description="User Biography",
    )
    phone_number: str | None = Field(
        example="+1234567890",
        description="Valid Phone Number",
    )
    date_of_birth: datetime.date | None = Field(
        example="1990-01-01",
        description="User's Birth Date",
    )
    gender: str | None = Field(
        example="male",
        description="User's Gender",
    )

    # Avatar
    avatar_url: str | None = Field(
        example="https://example.com/avatar.jpg",
        description="URL to User's Avatar",
    )

    # Location Information
    country: str | None = Field(
        example="United States",
        description="User's Country",
    )
    city: str | None = Field(
        example="New York",
        description="User's City",
    )
    timezone: str | None = Field(
        example="America/New_York",
        description="User's Timezone",
    )

    # Timestamps
    created_at: datetime.datetime = Field(
        ...,
        example="2025-07-21T08:56:30.123000+00:00",
        description="Profile Creation Timestamp",
    )
    updated_at: datetime.datetime = Field(
        ...,
        example="2025-07-21T09:30:30.123000+00:00",
        description="Last Update Timestamp",
    )

    # Model Dump
    def model_dump(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> dict:
        """
        Model Dump

        This Method Overrides the Default Model Dump Method to Convert DateTime Objects to ISO Format

        Args:
            *args (tuple[Any, ...]): Positional Arguments
            **kwargs (dict[str, Any]): Keyword Arguments

        Returns:
            dict: Model Dump Data
        """

        # Get Model Dump Data
        data = super().model_dump(*args, **kwargs)

        # Convert DateTime Objects to ISO Format
        for field in ["date_of_birth", "created_at", "updated_at"]:
            # Get Field Value
            value = getattr(self, field)

            # If Field Value is a DateTime Object
            if isinstance(value, (datetime.datetime)):
                # Convert to UTC and ISO Format
                data[field] = (
                    value.astimezone(datetime.UTC).replace(microsecond=(value.microsecond // 1000) * 1000).isoformat()
                )

            # if Field Value is a Date Object
            elif isinstance(value, (datetime.date)):
                # Convert to DateTime Object
                data[field] = value.isoformat()

        # Return Model Dump Data
        return data


# Exports
__all__: list[str] = ["Profile", "ProfileResponse"]
