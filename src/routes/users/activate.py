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
from src.models.users import User, UserResponse
from src.routes.users.base import router


# Internal Function to Send Activated Email
async def _send_activated_email(user: User) -> None:
    """
    Send Activated Email

    Args:
        user (User): User Instance
    """

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Remove Activation Token from Redis
        await redis.delete(f"activation_token:{user.id}")

    # Create Login Link
    login_link: str = f"{settings.PROJECT_DOMAIN}/api/login"

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "login_link": login_link,
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "activated.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject="Account Activated Successfully",
        html_content=html_content,
    )


# User Activate Endpoint
@router.get(
    path="/activate",
    status_code=status.HTTP_200_OK,
    summary="User Activation Endpoint",
    description="""
    Activate a User Account.

    This Endpoint Allows a User to Activate Their Account by Providing:
    - Activation Token (Query Parameter)
    """,
    name="User Activate",
    responses={
        status.HTTP_200_OK: {
            "description": "User Activated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Successful Activation": {
                            "summary": "Successful Activation",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "username": "john_doe",
                                "email": "john_doe@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "is_active": True,
                                "is_staff": False,
                                "is_superuser": False,
                                "date_joined": "2025-07-21T20:58:34.273000+00:00",
                                "last_login": "2025-07-21T21:58:34.273000+00:00",
                                "updated_at": "2025-07-21T21:30:34.273000+00:00",
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
                                "detail": "Invalid Activation Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Activation Token",
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
                        "Already Activated": {
                            "summary": "Already Activated",
                            "value": {
                                "detail": "User Already Activated",
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
                        "Activation Failed": {
                            "summary": "Activation Failed",
                            "value": {
                                "detail": "Failed to Activate User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def activate_user(token: str) -> JSONResponse:
    """
    Activate User

    Args:
        token (str): Activation Token

    Returns:
        JSONResponse: UserResponse with User Data
    """

    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=token,
            key=settings.ACTIVATION_JWT_SECRET,
            algorithms=[settings.ACTIVATION_JWT_ALGORITHM],
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
            content={"detail": "Invalid Activation Token"},
        )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get(f"activation_token:{payload['sub']}")

    # If Token Not Found
    if not stored_token:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Activation Token"},
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

        # If User Already Activated
        if existing_user["is_active"]:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "User Already Activated"},
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
                    "is_active": True,
                    "updated_at": updated_at,
                },
            },
        )

    # If User Not Activated
    if response.modified_count == 0:
        # Return Internal Server Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Activate User"},
        )

    # Update existing_user with activated status
    existing_user["is_active"] = True
    existing_user["updated_at"] = updated_at

    # Create User Instance
    user: User = User(**existing_user)

    # Send Activated Email
    await _send_activated_email(user=user)

    # Prepare Response Data
    response_data: dict = {key: value for key, value in user.model_dump().items() if key != "password"}

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["activate_user"]
