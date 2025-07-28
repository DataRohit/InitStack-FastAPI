# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import UpdateResult

# Local Imports
from config.mongodb import get_async_mongodb
from src.models.profiles import Profile, ProfileUpdateRequest
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User


# Update Profile
async def update_profile_handler(request: ProfileUpdateRequest, current_user: User) -> JSONResponse:
    """
    Update a Profile

    Args:
        request (ProfileUpdateRequest): ProfileUpdateRequest Containing Profile Data

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

        # Create and Validate Profile
        profile: Profile = Profile(
            user_id=current_user.id,
            **request.model_dump(by_alias=True),
        )

        # Update Profile
        result: UpdateResult | None = await mongo_collection.update_one(
            filter={
                "user_id": current_user.id,
            },
            update={
                "$set": profile.model_dump(by_alias=True),
            },
        )

        # If Update Failed
        if not result or result.modified_count == 0:
            # Return Internal Server Error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to Update Profile"},
            )

        # Return Response with ProfileResponse Model
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ProfileResponse(**profile.model_dump()).model_dump(mode="json"),
        )


# Exports
__all__: list[str] = [
    "update_profile_handler",
]
