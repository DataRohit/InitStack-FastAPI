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
from src.models.users import User, UserResetPasswordConfirmRequest
from src.routes.users.base import router


# Internal Function to Send Reset Password Confirm Email
async def _send_reset_password_confirm_email(user: User) -> None:
    """
    Send Reset Password Confirm Email

    Args:
        user (User): User Instance
    """

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Remove Reset Password Token from Redis
        await redis.delete(f"reset_password_token:{user.id}")

    # Create Login Link
    login_link: str = f"{settings.PROJECT_DOMAIN}/api/login"

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "login_link": login_link,
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(
        Path(__file__).parent.parent.parent / "templates" / "users" / "reset_password_confirm.html",
    )

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject="Password Reset Successfully",
        html_content=html_content,
    )


# User Reset Password Confirm Endpoint
@router.post(
    path="/reset_password_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Reset Password Confirm Endpoint",
    description="""
    Confirms User Reset Password Process.

    This Endpoint Allows a User to Confirm the Reset Password Process by Providing:
    - Reset Password Request (Password and Password Confirmation)
    - Reset Password Token (Query Parameter)

    Returns:
        JSONResponse: Success Message With 200 Status
    """,
    name="User Reset Password Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "User Reset Password Confirmed Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Password Reset Confirmed": {
                            "summary": "Password Reset Confirmed",
                            "value": {
                                "detail": "User Reset Password Confirmed Successfully",
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
                                "detail": "Invalid Reset Password Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Reset Password Token",
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
                        "Inactive User": {
                            "summary": "Inactive User",
                            "value": {
                                "detail": "User Is Not Active",
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
                        "Reset Failed": {
                            "summary": "Reset Failed",
                            "value": {
                                "detail": "Failed To Reset Password",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def reset_password_confirm(request: UserResetPasswordConfirmRequest, token: str) -> JSONResponse:
    """
    Resets User Password.

    Args:
        request (UserResetPasswordConfirmRequest): Reset Password Confirm Request
        token (str): Reset Password Token

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=token,
            key=settings.RESET_PASSWORD_JWT_SECRET,
            algorithms=[settings.RESET_PASSWORD_JWT_ALGORITHM],
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
            content={"detail": "Invalid Reset Password Token"},
        )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get(f"reset_password_token:{payload['sub']}")

    # If Token Not Found
    if not stored_token:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Reset Password Token"},
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
                content={"detail": "User Is Not Active"},
            )

        # Calculated Updated At
        updated_at: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

        # Create User Instance
        user: User = User(**existing_user)

        # Set New Password
        user.set_password(request.password)

        # Set Updated At
        user.updated_at = updated_at

        # Update User in Database
        response: UpdateResult = await mongo_collection.update_one(
            filter={
                "_id": payload["sub"],
            },
            update={
                "$set": {
                    "password": user.password,
                    "updated_at": user.updated_at,
                },
            },
        )

    # If User Not Updated
    if response.modified_count == 0:
        # Return Internal Server Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Reset Password"},
        )

    # Send Reset Password Confirm Email
    await _send_reset_password_confirm_email(user=user)

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "User Reset Password Confirmed Successfully",
        },
    )


# Exports
__all__ = [
    "reset_password_confirm",
]
