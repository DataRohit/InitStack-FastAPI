# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_async_mongodb
from src.models.users import UserCheckUsernameRequest
from src.routes.users.base import router


# User Check Username Endpoint
@router.post(
    path="/check_username",
    status_code=status.HTTP_200_OK,
    summary="Check Username Availability",
    description="""
    Check if a Username is Available.

    This Endpoint Allows Checking if a Given Username is Already Taken by Another User.
    It Returns a Success Response if the Username is Available, or a Conflict Response if it is Already in Use.
    """,
    name="Check Username",
    responses={
        status.HTTP_200_OK: {
            "description": "Username is Available",
            "content": {
                "application/json": {
                    "examples": {
                        "Username Available": {
                            "summary": "Username Available",
                            "value": {"detail": "Username is Available"},
                        },
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Username Already Exists",
            "content": {
                "application/json": {
                    "examples": {
                        "Username Taken": {
                            "summary": "Username Taken",
                            "value": {"detail": "Username Already Exists"},
                        },
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid Request",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Username Format": {
                            "summary": "Invalid Username Format",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "username",
                                        "reason": "Username Must Be 8+ Characters, Using Lowercase Letters, Numbers, @, -, _",  # noqa: E501
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
                        "Internal Server Error": {
                            "summary": "Internal Server Error",
                            "value": {
                                "detail": "Internal Server Error",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def check_username(request: UserCheckUsernameRequest) -> JSONResponse:
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
__all__: list[str] = ["check_username"]
