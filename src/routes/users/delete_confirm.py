# Standard Library Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import DeleteResult

# Local Imports
from config.mailer import render_template, send_email
from config.mongodb import get_async_mongodb
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User
from src.tasks.profiles import delete_profile_task


# Internal Function to Send Deleted Email
async def _send_deleted_email(user: User) -> None:
    """
    Send Deleted Email

    Args:
        user (User): User Instance
    """

    # Remove Deletion Token from Redis
    await redis_manager.delete(
        key=f"deletion_token:{user.id}",
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "delete_confirm.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject="Account Deleted Successfully",
        html_content=html_content,
    )


# Delete User
async def delete_user_confirm_handler(token: str) -> JSONResponse:
    """
    Delete User

    Args:
        token (str): Deletion Token

    Returns:
        JSONResponse: UserResponse with User Data
    """

    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=token,
            key=settings.DELETE_JWT_SECRET,
            algorithms=[settings.DELETE_JWT_ALGORITHM],
            verify=True,
            audience=settings.PROJECT_NAME,
            issuer=settings.PROJECT_NAME,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
                "strict_aud": True,
            },
        )

    except jwt.InvalidTokenError:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Deletion Token"},
        )

    # Get Token from Redis
    stored_token: str | None = await redis_manager.get(
        key=f"deletion_token:{payload['sub']}",
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

    # If Token Not Found
    if not stored_token:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Deletion Token"},
        )

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Get User by ID
        existing_user: dict | None = await mongo_collection.find_one(
            filter={
                "_id": payload["sub"],
            },
        )

        # If User Not Found
        if not existing_user:
            # Return Not Found Response
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User Not Found"},
            )

        # If User Is Not Active
        if not existing_user["is_active"]:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"message": "User Is Not Active"},
            )

        # Delete User from Database
        response: DeleteResult = await mongo_collection.delete_one(
            filter={
                "_id": payload["sub"],
            },
        )

        # If User Not Deleted
        if response.deleted_count == 0:
            # Return Internal Server Error Response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to Delete User"},
            )

        # Delete User Profile
        delete_profile_task.delay(user_id=payload["sub"])

    # Create User Instance
    user: User = User(**existing_user)

    # Send Deleted Email
    await _send_deleted_email(user=user)

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "User Deleted Successfully",
        },
    )


# Exports
__all__: list[str] = ["delete_user_confirm_handler"]
