# Standard Library Imports
from typing import Annotated

# Third-Party Imports
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import InsertOneResult

# Local Imports
from config.jwt_auth import get_current_user
from config.mongodb import get_async_mongodb
from src.models.profiles import Profile, ProfileCreateRequest
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User
from src.routes.profiles.base import router


# Create Profile Endpoint
@router.post(
    path="/create",
    status_code=status.HTTP_201_CREATED,
    summary="Create Profile Endpoint",
    description="""
    Create a New User Profile.

    This Endpoint Allows a Logged-in User to Create Their Profile by Providing:
    - bio (Optional)
    - phone_number (Optional)
    - date_of_birth (Optional)
    - gender (Optional)
    - country (Optional)
    - city (Optional)
    - timezone (Optional)
    """,
    name="Create Profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Profile Created Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "New Profile": {
                            "summary": "New Profile",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "user_id": "687ea9fa53bf34da640e4ef5",
                                "bio": "Software developer and open source enthusiast",
                                "phone_number": "+1234567890",
                                "date_of_birth": "1990-01-01",
                                "gender": "male",
                                "avatar_url": "http://localhost:8080/dicebear/9.x/avataaars/png?seed=admin&accessories=&eyebrows=default%2CdefaultNatural&eyes=default%2Chappy%2Cwink&mouth=default%2Csmile",
                                "country": "United States",
                                "city": "New York",
                                "timezone": "America/New_York",
                                "created_at": "2025-07-21T20:58:34.273000+00:00",
                                "updated_at": "2025-07-21T21:30:34.273000+00:00",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Authentication Credentials",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "examples": {
                        "Authentication Required": {
                            "summary": "Authentication Required",
                            "value": {
                                "detail": "Authentication Required",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Exists": {
                            "summary": "Profile Already Exists",
                            "value": {
                                "detail": "Profile Already Exists",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Unprocessable Entity",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Phone Number": {
                            "summary": "Invalid Phone Number",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "phone_number",
                                        "reason": "Phone Number Must Be Between 7 and 15 Digits",
                                    },
                                ],
                            },
                        },
                        "Invalid Date of Birth": {
                            "summary": "Invalid Date of Birth",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "date_of_birth",
                                        "reason": "Date of Birth Cannot Be in the Future",
                                    },
                                ],
                            },
                        },
                        "Invalid Gender": {
                            "summary": "Invalid Gender",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "gender",
                                        "reason": "Gender Must Be One of: male, female, non-binary, other",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Creation Failed": {
                            "summary": "Profile Creation Failed",
                            "value": {
                                "detail": "Failed to Create Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def create_profile(
    request: ProfileCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """
    Create Profile

    Args:
        request (ProfileCreateRequest): ProfileCreateRequest Containing Profile Data
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: ProfileResponse with Profile Data
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("profiles")

        # Check If Profile Already Exists
        existing_profile: dict | None = await mongo_collection.find_one(
            filter={
                "user_id": current_user.id,
            },
        )

        # If Profile Already Exists
        if existing_profile:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "Profile Already Exists"},
            )

        # Create and Validate Profile
        profile: Profile = Profile(
            user_id=current_user.id,
            **request.model_dump(by_alias=True),
        )

        # Save to Database
        result: InsertOneResult | None = await mongo_collection.insert_one(
            document=profile.model_dump(by_alias=True),
        )

    # If Insertion Failed
    if not result:
        # Return Internal Server Error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Create Profile"},
        )

    # Return Response with ProfileResponse Model
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=ProfileResponse(**profile.model_dump()).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = [
    "create_profile",
]
