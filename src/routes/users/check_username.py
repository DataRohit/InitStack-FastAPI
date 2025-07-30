# Standard Library Imports

# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_async_mongodb
from src.models.users import UserCheckUsernameRequest


# Check Username Availability
async def check_username_handler(request: UserCheckUsernameRequest) -> JSONResponse:
    """
    Check Username Availability

    Args:
        request (UserCheckUsernameRequest): UserCheckUsernameRequest Containing Username to Check

    Returns:
        JSONResponse: Success or Error Response Indicating Username Availability
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Check If Username Already Exists
        existing_user: dict | None = await mongo_collection.find_one(
            filter={
                "username": request.username,
            },
        )

    # If Username Already Exists
    if existing_user:
        # Return Conflict Response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Username Already Exists",
            },
        )

    # If Username is Available
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Username is Available",
        },
    )


# Exports
__all__: list[str] = ["check_username_handler"]
