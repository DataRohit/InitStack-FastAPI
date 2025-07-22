# Standard Library Imports
import datetime
import re
from typing import ClassVar

# Third-Party Imports
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError, VerifyMismatchError
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import PyMongoError
from pymongo.results import InsertOneResult

# Initialize Password Hasher
ph = PasswordHasher()


# User Model
class User(BaseModel):
    """
    User Model

    This Model Defines the Structure of User Data in the System.

    Attributes:
        id (str | None): Unique User Identifier
        username (str): Unique Username with Specific Formatting
        first_name (str): User's First Name
        last_name (str): User's Last Name
        email (str): Valid Email Address
        password (str): Hashed Password
        is_active (bool): Account Activation Status
        is_staff (bool): Staff Access Status
        is_superuser (bool): Admin Access Status
        date_joined (datetime.datetime): Account Creation Timestamp
        last_login (datetime.datetime | None): Last Login Timestamp
        updated_at (datetime.datetime): Last Update Timestamp
    """

    # Model Configuration
    model_config: ClassVar[dict] = {
        "arbitrary_types_allowed": True,
        "validate_by_name": True,
        "extra": "forbid",
    }

    # User Identifier
    id: str | None = Field(
        default_factory=lambda: str(ObjectId()),
        alias="_id",
        example="507f1f77bcf86cd799439011",
        description="Unique User Identifier",
    )

    # Authentication Fields
    username: str = Field(
        ...,
        example="john_doe",
        description="Unique Username (Lowercase, Alphanumeric with @-_)",
    )
    email: EmailStr = Field(
        ...,
        example="john_doe@example.com",
        description="Valid Email Address",
    )
    password: str = Field(
        ...,
        example="$argon2id$v=19$m=65536,t=3,p=4$MIIRqgvgQbgj220jfp0MPA$YfwJSVjtjSU0zzV/P3S9nnQ/USre2wvJMjfCIjrTQbg",
        description="Hashed Password",
    )

    # Personal Information
    first_name: str = Field(
        ...,
        example="John",
        description="User's First Name (Alphabetic Characters Only)",
    )
    last_name: str = Field(
        ...,
        example="Doe",
        description="User's Last Name (Alphabetic Characters Only)",
    )

    # Status Flags
    is_active: bool = Field(
        default=False,
        example=True,
        description="Account Activation Status",
    )
    is_staff: bool = Field(
        default=False,
        example=False,
        description="Staff Access Status",
    )
    is_superuser: bool = Field(
        default=False,
        example=False,
        description="Admin Access Status",
    )

    # Timestamps
    date_joined: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        example="2025-07-21T08:56:30.123456+00:00",
        description="Account Creation Timestamp",
    )
    last_login: datetime.datetime | None = Field(
        default=None,
        example="2025-07-21T09:56:30.123456+00:00",
        description="Last Login Timestamp",
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        example="2025-07-21T09:30:30.123456+00:00",
        description="Last Update Timestamp",
    )

    # Set Password
    def set_password(self, password: str) -> None:
        """
        Set User Password

        Hashes and Stores Password

        Args:
            password (str): Plain Text Password

        Raises:
            HashingError: If Password Hashing Fails
        """

        try:
            # Hash Password
            self.password = ph.hash(password=password)

        except HashingError as e:
            # Set Error Message
            msg = "Failed to Hash Password"

            # Raise HashingError
            raise HashingError(msg) from e

    # Verify Password
    def verify_password(self, password: str) -> bool:
        """
        Verify User Password

        Compares Input Password with Stored Hash

        Args:
            password (str): Plain Text Password to Verify

        Returns:
            bool: True if Password Matches, False Otherwise

        Raises:
            VerificationError: If Password Verification Fails
        """

        try:
            # Verify Password
            return ph.verify(hash=self.password, password=password)

        except (VerifyMismatchError, VerificationError, InvalidHashError):
            # Return False
            return False

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

    # Name Validation
    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validate Name Format

        Ensures Name Contains Only Letters

        Args:
            value (str): Name to Validate

        Returns:
            str: Validated Name

        Raises:
            ValueError: If Name Contains Invalid Characters
        """

        # If Name Contains Invalid Characters
        if not re.fullmatch(r"[A-Za-z]{3,30}", value):
            # Raise ValueError
            raise ValueError({"reason": "Name Must Be 3-30 Letters Only, No Spaces or Special Characters"})

        # Return Validated Name
        return value

    # Password Validation
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Validate Password Complexity

        Ensures Password Meets Complexity Requirements:
        - At Least 1 Uppercase Letter
        - At Least 1 Lowercase Letter
        - At Least 1 Number
        - At Least 1 Special Character

        Args:
            value (str): Password to Validate

        Returns:
            str: Validated Password

        Raises:
            ValueError: If Password Doesn't Meet Complexity Requirements
        """

        # If Password Doesn't Meet Complexity Requirements
        if not re.fullmatch(r"(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}", value):
            # Raise ValueError
            raise ValueError(
                {
                    "reason": "Password Must Be At Least 8 Characters Long And Contain 1 Uppercase Letter, 1 Lowercase Letter, 1 Number & 1 Special Character",  # noqa: E501
                },
            )

        # Return Validated Password
        return value

    # Create Indexes
    @classmethod
    async def create_indexes(cls, collection: AsyncCollection) -> None:
        """
        Create Database Indexes

        Creates indexes for:
        - id (unique)
        - username (unique)
        - email (unique)
        - is_active + is_staff + is_superuser
        - date_joined
        - last_login
        - updated_at

        Args:
            collection (AsyncCollection): MongoDB Collection Instance

        Raises:
            PyMongoError: If Index Creation Fails
        """

        try:
            # Create Single Field Indexes
            await collection.create_index("username", unique=True)
            await collection.create_index("email", unique=True)

            # Create Status Compound Index
            await collection.create_index([("is_active", 1), ("is_staff", 1), ("is_superuser", 1)])

            # Create Date Indexes
            await collection.create_index("date_joined")
            await collection.create_index("last_login")
            await collection.create_index("updated_at")

        except PyMongoError as e:
            # Raise PyMongoError
            msg: str = f"Index Creation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

    # Create User
    @classmethod
    async def create(cls, collection: AsyncCollection, user_data: dict) -> "User":
        """
        Create New User

        Args:
            collection (AsyncCollection): MongoDB Collection Instance
            user_data (dict): User Data Dictionary

        Returns:
            User: Created User Instance

        Raises:
            ValueError: If Validation Fails
            PyMongoError: If Database Operation Fails
        """

        # Validate and Create User Instance
        user: User = cls(**user_data)

        # Insert into Database
        result: InsertOneResult = await collection.insert_one(user.model_dump(by_alias=True))

        # Set User ID
        user.id: ObjectId = result.inserted_id

        # Return User
        return user

    # Get User by ID
    @classmethod
    async def get_by_id(cls, collection: AsyncCollection, user_id: str) -> "User | None":
        """
        Get User by ID

        Args:
            collection (AsyncCollection): MongoDB Collection Instance
            user_id (str): User ID to Retrieve

        Returns:
            User | None: User Instance if Found, Else None
        """

        # Find User by ID
        user_data: dict | None = await collection.find_one({"_id": user_id})

        # Return User Instance if Found
        return cls(**user_data) if user_data else None

    # Get User by Identifier (Username or Email)
    @classmethod
    async def get_by_identifier(cls, collection: AsyncCollection, identifier: str) -> "User | None":
        """
        Get User by Username or Email

        Args:
            collection (AsyncCollection): MongoDB Collection Instance
            identifier (str): Username or Email to Search For

        Returns:
            User | None: User Instance if Found, Else None
        """

        # Find User by Username or Email
        user_data: dict | None = await collection.find_one({"$or": [{"username": identifier}, {"email": identifier}]})

        # Return User Instance if Found
        return cls(**user_data) if user_data else None

    # Update User
    @classmethod
    async def update(cls, collection: AsyncCollection, update_data: dict) -> None:
        """
        Update User

        Args:
            collection (AsyncCollection): MongoDB Collection Instance
            update_data (dict): Data to Update

        Raises:
            ValueError: If Validation Fails
            PyMongoError: If Database Operation Fails
        """

        # Traverse Update Data
        for field, value in update_data.items():
            # Set Attribute Value
            setattr(cls, field, value)

        # Update Timestamp
        cls.updated_at: datetime.datetime = datetime.datetime.now(datetime.UTC)

        # Update in Database
        await collection.update_one({"_id": cls.id}, {"$set": cls.model_dump(exclude_unset=True)})

    # Delete User by ID
    @classmethod
    async def delete_by_id(cls, collection: AsyncCollection, user_id: str) -> None:
        """
        Delete User

        Args:
            collection (AsyncCollection): MongoDB Collection Instance

        Raises:
            PyMongoError: If Database Operation Fails
        """

        # Delete from Database
        await collection.delete_one({"_id": user_id})

    # Delete User by Identifier (Username or Email)
    @classmethod
    async def delete_by_identifier(cls, collection: AsyncCollection, identifier: str) -> None:
        """
        Delete User

        Args:
            collection (AsyncCollection): MongoDB Collection Instance

        Raises:
            PyMongoError: If Database Operation Fails
        """

        # Delete from Database
        await collection.delete_one({"$or": [{"username": identifier}, {"email": identifier}]})

    # Delete Inactive Users
    @classmethod
    async def delete_inactive_users(cls, collection: AsyncCollection) -> None:
        """
        Delete Inactive Users

        Args:
            collection (AsyncCollection): MongoDB Collection Instance

        Raises:
            PyMongoError: If Database Operation Fails
        """

        # Delete All Users where date_joined Older than 30 Minutes & is_active is False
        await collection.delete_many(
            {
                "date_joined": {"$lt": datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=1800)},
                "is_active": False,
            },
        )


# User Response Model
class UserResponse(BaseModel):
    """
    User Response Model

    This Model Defines the Structure of User Data Returned in API Responses.
    """

    # Model Configuration
    model_config: ClassVar[dict] = {"arbitrary_types_allowed": True, "extra": "forbid"}

    # Identification Fields
    id: str = Field(
        ...,
        example="507f1f77bcf86cd799439011",
        description="Unique User Identifier",
    )
    username: str = Field(
        ...,
        example="john_doe",
        description="Unique Username with Specific Formatting",
    )
    email: EmailStr = Field(
        ...,
        example="john@example.com",
        description="Valid Email Address",
    )

    # Personal Information
    first_name: str = Field(
        ...,
        example="John",
        description="User's First Name",
    )
    last_name: str = Field(
        ...,
        example="Doe",
        description="User's Last Name",
    )

    # Status Flags
    is_active: bool = Field(
        example=True,
        description="Account Activation Status",
    )
    is_staff: bool = Field(
        example=False,
        description="Staff Access Status",
    )
    is_superuser: bool = Field(
        example=False,
        description="Admin Access Status",
    )

    # Timestamps
    date_joined: datetime.datetime = Field(
        ...,
        example="2025-07-21T18:24:52.443934+00:00",
        description="Account Creation Timestamp",
    )
    last_login: datetime.datetime | None = Field(
        example="2025-07-21T08:56:30.123456+00:00",
        description="Last Login Timestamp",
    )
    updated_at: datetime.datetime = Field(
        ...,
        example="2025-07-21T18:24:52.443939+00:00",
        description="Last Update Timestamp",
    )


# Exports
__all__: list[str] = ["User", "UserResponse"]
