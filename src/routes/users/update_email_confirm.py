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
from src.models.users.update_email import UserUpdateEmailRequest
from src.routes.users.base import router


# Internal Function to Send Update Email Success Email
async def _send_update_email_success_email(user: User, new_email: str) -> None:
    """
    Send Update Email Success Email

    Args:
        user (User): User Instance
        new_email (str): The New Email Address
    """

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Remove Update Email Token from Redis
        await redis.delete(f"update_email_token:{user.id}")

    # Create Login Link
    login_link: str = f"{settings.PROJECT_DOMAIN}/api/login"

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": new_email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "login_link": login_link,
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "update_email_success.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=new_email,
        subject="Email Updated Successfully",
        html_content=html_content,
    )


# User Update Email Confirm Endpoint
@router.post(
    path="/update_email_confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm User Email Update",
    description="""
    Confirm User Email Update.

    This Endpoint Allows a User to Confirm Their Email Update by Providing:
    - Token (Query Parameter)
    - New Email (Request Body)
    """,
    name="Update Email Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "Email Updated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Email Updated": {
                            "summary": "Email Updated",
                            "value": {
                                "message": "Email Updated Successfully.",
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
                                "detail": "Invalid Token",
                            },
                        },
                        "Token Expired": {
                            "summary": "Token Expired",
                            "value": {
                                "detail": "Token Expired",
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
                        "Email Already Exists": {
                            "summary": "Email Already Exists",
                            "value": {
                                "detail": "New Email Already Exists",
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
                        "Email Update Failed": {
                            "summary": "Email Update Failed",
                            "value": {
                                "detail": "Failed To Confirm Email Update",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_email_confirm(
    token: str,
    request: UserUpdateEmailRequest,
) -> JSONResponse:
    """
    Confirm User Email Update.

    Args:
        token (str): Update Email Token
        request (UserUpdateEmailRequest): UserUpdateEmailRequest Containing New Email

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=token,
            key=settings.UPDATE_EMAIL_JWT_SECRET,
            algorithms=[settings.UPDATE_EMAIL_JWT_ALGORITHM],
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
            content={"detail": "Invalid Update Email Token"},
        )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get(f"update_email_token:{payload['sub']}")

    # If Token Not Found
    if not stored_token:
        # Return Unauthorized Response
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Update Email Token"},
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

        # If New Email Already Exists
        if await mongo_collection.find_one({"email": request.email}):
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "Email Already Exists"},
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
                    "email": request.email,
                    "updated_at": updated_at,
                },
            },
        )

    # If User Not Updated
    if response.modified_count == 0:
        # Return Internal Server Error Response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Update Email"},
        )

    # Update existing_user with new email
    existing_user["email"] = request.email
    existing_user["updated_at"] = updated_at

    # Create User Instance
    user: User = User(**existing_user)

    # Send Update Email Success Email
    await _send_update_email_success_email(user=user, new_email=request.email)

    # Return Response with Success Message
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Email Updated Successfully",
        },
    )


# Exports
__all__: list[str] = ["update_email_confirm"]
