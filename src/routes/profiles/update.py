# Standard Library Imports
import datetime
from typing import Annotated

# Third-Party Imports
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import UpdateResult

# Local Imports
from config.jwt_auth import get_current_user
from config.mongodb import get_async_mongodb
from src.models.profiles import Profile, ProfileUpdateRequest
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User
from src.routes.profiles.base import router


# Update Profile Endpoint
@router.put(
    path="/update",
    status_code=status.HTTP_200_OK,
    summary="Update Profile Endpoint",
    description="""
    Update User Profile.

    This Endpoint Allows a Logged-in User to Update Their Profile by Providing:
    - bio (Optional)
    - phone_number (Optional)
    - date_of_birth (Optional)
    - gender (Optional)
    - country (Optional)
    - city (Optional)
    - timezone (Optional)
    """,
    name="Update Profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Profile Updated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Updated Profile": {
                            "summary": "Updated Profile",
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
                        "Update Failed": {
                            "summary": "Profile Update Failed",
                            "value": {
                                "detail": "Failed to Update Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """
    Update Profile

    Args:
        request (ProfileUpdateRequest): ProfileUpdateRequest Containing Profile Data
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

        # Prepare Update Data with Timestamp
        update_data: dict = {
            **request.model_dump(by_alias=True, exclude_unset=True),
            "updated_at": datetime.datetime.now(tz=datetime.UTC),
        }

        # Update Profile in Database
        result: UpdateResult = await mongo_collection.update_one(
            filter={"user_id": current_user.id},
            update={"$set": update_data},
        )

        # If Update Failed
        if result.modified_count == 0:
            # Return Internal Server Error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to Update Profile"},
            )

        # Create Updated Profile for Response
        updated_profile_data: dict = {**profile_data, **update_data}
        updated_profile: Profile = Profile(**updated_profile_data)

        # Return Response with ProfileResponse Model
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ProfileResponse(**updated_profile.model_dump()).model_dump(mode="json"),
        )


# Exports
__all__: list[str] = [
    "update_profile",
]
