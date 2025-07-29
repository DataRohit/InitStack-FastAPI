# Standard Imports
import datetime

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
    "update_profile_handler",
]
