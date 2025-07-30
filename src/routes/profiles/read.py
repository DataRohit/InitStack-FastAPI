# Standard Library Imports
from typing import Annotated

# Third-Party Imports
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.jwt_auth import get_current_user
from config.mongodb import get_async_mongodb
from src.models.profiles import Profile
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User
from src.routes.profiles.base import router


# Read Profile Endpoint
@router.get(
    path="/get",
    status_code=status.HTTP_200_OK,
    summary="Read Profile Endpoint",
    description="""
    Read User Profile.

    This Endpoint Allows a Logged-in User to Read Their Profile.
    """,
    name="Read Profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Profile Read Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Data": {
                            "summary": "Profile Data",
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
        status.HTTP_404_NOT_FOUND: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Not Found": {
                            "summary": "Profile Not Found",
                            "value": {
                                "detail": "Profile Not Found",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def read_profile(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Read Profile

    Args:
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: ProfileResponse with Profile Data
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("profiles")

        # Get Profile
        profile_data: dict | None = await mongo_collection.find_one(
            filter={"user_id": current_user.id},
        )

    # If Profile Not Found
    if not profile_data:
        # Return Not Found Response
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Profile Not Found"},
        )

    # Create Profile Instance for Validation
    profile: Profile = Profile(**profile_data)

    # Return Response with ProfileResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ProfileResponse(**profile.model_dump()).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = [
    "read_profile",
]
