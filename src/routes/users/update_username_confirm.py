# Standard Library Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import UpdateResult

# Local Imports
from config.mailer import render_template, send_email
from config.mongodb import get_async_mongodb
from config.redis_cache import get_async_redis
from config.settings import settings
from src.models.users import User
from src.models.users.update_username_confirm import UserUpdateUsernameConfirmRequest
from src.routes.users.base import router


# Internal Function to Send Update Username Success Email
async def _send_update_username_success_email(user: User, new_username: str) -> None:
    """
    Send Update Username Success Email

    Args:
        user (User): User Instance
        new_username (str): The New Username
    """

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Remove Update Username Token from Redis
        await redis.delete(f"update_username_token:{user.id}")

    # Create Login Link
    login_link: str = f"{settings.PROJECT_DOMAIN}/api/login"

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "new_username": new_username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "login_link": login_link,
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(
        Path(__file__).parent.parent.parent / "templates" / "users" / "update_username_success.html",
    )

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject="Username Updated Successfully",
        html_content=html_content,
    )


# User Update Username Confirm Endpoint
@router.post(
    path="/update_username_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Update Username Confirmation Endpoint",
    description="""
    Confirm User Update Username Process.

    This Endpoint Allows a User to Confirm Their Username Update by Providing:
    - Update Username Token (Query Parameter)
    - New Username (Request Body)
    """,
    name="User Update Username Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "Username Updated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Success": {
                            "summary": "Success",
                            "value": {
                                "detail": "Username Updated Successfully",
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
                                "detail": "Invalid Update Username Token",
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
                        "User Not Found": {
                            "summary": "User Not Found",
                            "value": {
                                "detail": "User Not Found",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "examples": {
                        "Username Exists": {
                            "summary": "Username Exists",
                            "value": {
                                "detail": "Username Already Exists",
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
                        "Missing Token": {
                            "summary": "Missing Token",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "token",
                                        "reason": "Field Required",
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
                        "Failed to Update Username": {
                            "summary": "Failed to Update Username",
                            "value": {
                                "detail": "Failed to Update Username",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_username_confirm(
    token: str,
    request: UserUpdateUsernameConfirmRequest,
) -> JSONResponse:
    """
    Confirm User Update Username

    Args:
        token (str): Update Username Token
        request (UserUpdateUsernameConfirmRequest): UserUpdateUsernameConfirmRequest Containing New Username

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=token,
            key=settings.UPDATE_USERNAME_JWT_SECRET,
            algorithms=[settings.UPDATE_USERNAME_JWT_ALGORITHM],
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
            content={"detail": "Invalid Update Username Token"},
        )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get(f"update_username_token:{payload['sub']}")

    # If Token Not Found
    if not stored_token:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Update Username Token"},
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

        # If New Username Already Exists
        if await mongo_collection.find_one({"username": request.username}):
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "Username Already Exists"},
            )

        # Calculated Updated At
        updated_at: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

        # Update User in Database
        response: UpdateResult = await mongo_collection.update_one(
            filter={
                "_id": payload["sub"],
            },
            update={
                "$set": {
                    "username": request.username,
                    "updated_at": updated_at,
                },
            },
        )

    # If User Not Updated
    if response.modified_count == 0:
        # Return Internal Server Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Update Username"},
        )

    # Update existing_user with new username
    existing_user["username"] = request.username
    existing_user["updated_at"] = updated_at

    # Create User Instance
    user: User = User(**existing_user)

    # Send Update Username Success Email
    await _send_update_username_success_email(user=user, new_username=request.username)

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Username Updated Successfully",
        },
    )


# Exports
__all__: list[str] = ["update_username_confirm"]
