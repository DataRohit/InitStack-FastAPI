# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_async_mongodb
from src.models.profiles import Profile
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User


# Read Profile
async def read_profile_handler(current_user: User) -> JSONResponse:
    """
    Read a Profile

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

        # Create and Validate Profile
        profile: Profile = Profile(
            user_id=current_user.id,
            **profile,
        )

        # Return Response with ProfileResponse Model
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ProfileResponse(**profile.model_dump()).model_dump(mode="json"),
        )


# Exports
__all__: list[str] = [
    "read_profile_handler",
]
