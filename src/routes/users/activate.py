# Third-Party Imports
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
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User, UserResponse


# Internal Function to Send Activated Email
async def _send_activated_email(user: User) -> None:
    """
    Send Activated Email

    Args:
        user (User): User Instance
    """

    # Remove Activation Token from Redis
    await redis_manager.delete(
        key=f"activation_token:{user.id}",
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

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


# Activate User
async def activate_user_handler(token: str) -> JSONResponse:
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

    # Get Token from Redis
    stored_token: str | None = await redis_manager.get(
        key=f"activation_token:{payload['sub']}",
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

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
__all__: list[str] = ["activate_user_handler"]
