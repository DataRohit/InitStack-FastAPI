# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import DeleteResult

# Local Imports
from config.mongodb import get_async_mongodb
from src.models.users.base import User


# Delete Profile
async def delete_profile_handler(current_user: User) -> JSONResponse:
    """
    Delete a Profile

    Args:
        current_user (User): User Instance

    Returns:
        JSONResponse: ProfileResponse with Profile Data
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
    "delete_profile_handler",
]
