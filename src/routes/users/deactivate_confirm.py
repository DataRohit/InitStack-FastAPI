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
from src.routes.users.base import router


# Internal Function to Send Deactivated Email
async def _send_deactivated_email(user: User) -> None:
    """
    Send Deactivated Email

    Args:
        user (User): User Instance
    """

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Remove Deactivation Token from Redis
        await redis.delete("deactivation_token:{user.id}")

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
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "deactivate_confirm.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject="Account Deactivated Successfully",
        html_content=html_content,
    )


# User Deactivate Confirm Endpoint
@router.get(
    path="/deactivate_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Deactivate Confirm Endpoint",
    description="""
    Confirms User Deactivation Process.

    This Endpoint Allows a User to Confirm the Deactivation Process by Providing:
    - Deactivation Token (Query Parameter)
    """,
    name="User Deactivate Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "User Deactivated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Successful Deactivation": {
                            "summary": "Successful Deactivation",
                            "value": {
                                "detail": "User Deactivated Successfully",
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
                                "detail": "Invalid Deactivation Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Deactivation Token",
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
                        "Already Deactivated": {
                            "summary": "Already Deactivated",
                            "value": {
                                "detail": "User Already Deactivated",
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
                        "Deactivation Failed": {
                            "summary": "Deactivation Failed",
                            "value": {
                                "detail": "Failed To Deactivate User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def deactivate_user_confirm(token: str) -> JSONResponse:
    """
    Confirms User Deactivation Process.

    Args:
        token (str): Deactivation Token

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=token,
            key=settings.DEACTIVATE_JWT_SECRET,
            algorithms=[settings.DEACTIVATE_JWT_ALGORITHM],
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
            content={"detail": "Invalid Deactivation Token"},
        )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get("deactivation_token:{payload['sub']}")

    # If Token Not Found
    if not stored_token:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Deactivation Token"},
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

        # If User Already Deactivated
        if not existing_user["is_active"]:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "User Already Deactivated"},
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
                    "is_active": False,
                    "updated_at": updated_at,
                },
            },
        )

    # If User Not Deactivated
    if response.modified_count == 0:
        # Return Internal Server Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Deactivate User"},
        )

    # Update existing_user with deactivated status
    existing_user["is_active"] = False
    existing_user["updated_at"] = updated_at

    # Create User Instance
    user: User = User(**existing_user)

    # Send Deactivated Email
    await _send_deactivated_email(user=user)

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "User Deactivated Successfully",
        },
    )


# Exports
__all__: list[str] = ["deactivate_user_confirm"]
