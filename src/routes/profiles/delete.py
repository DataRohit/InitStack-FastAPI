# Standard Library Imports
from typing import Annotated

# Third-Party Imports
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import DeleteResult

# Local Imports
from config.jwt_auth import get_current_user
from config.mongodb import get_async_mongodb
from src.models.users.base import User
from src.routes.profiles.base import router


# Delete Profile Endpoint
@router.delete(
    path="/delete",
    status_code=status.HTTP_200_OK,
    summary="Delete Profile Endpoint",
    description="""
    Delete User Profile.

    This Endpoint Allows a Logged-in User to Delete Their Profile.
    """,
    name="Delete Profile",
    responses={
        status.HTTP_200_OK: {
            "description": "Profile Deleted Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Deleted": {
                            "summary": "Profile Deleted Successfully",
                            "value": {
                                "detail": "Profile Deleted Successfully",
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
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Deletion Failed": {
                            "summary": "Profile Deletion Failed",
                            "value": {
                                "detail": "Failed to Delete Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def delete_profile(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Delete Profile

    Args:
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: Confirmation of Profile Deletion
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("profiles")

        # Get Profile
        profile: dict | None = await mongo_collection.find_one(
            filter={
                "user_id": current_user.id,
            },
        )

        # If Profile Not Found
        if not profile:
            # Return Not Found Response
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Profile Not Found"},
            )

        # Delete Profile
        result: DeleteResult | None = await mongo_collection.delete_one(
            filter={
                "user_id": current_user.id,
            },
        )

        # If Deletion Failed
        if not result or result.deleted_count == 0:
            # Return Internal Server Error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to Delete Profile"},
            )

        # Return Response with ProfileResponse Model
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Profile Deleted Successfully"},
        )


# Exports
__all__: list[str] = [
    "delete_profile",
]
