# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import InsertOneResult

# Local Imports
from config.mongodb import get_async_mongodb
from src.models.profiles import Profile, ProfileCreateRequest
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User


# Create Profile
async def create_profile_handler(request: ProfileCreateRequest, current_user: User) -> JSONResponse:
    """
    Create a New Profile

    Args:
        request (ProfileCreateRequest): ProfileCreateRequest Containing Profile Data

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
    "create_profile_handler",
]
