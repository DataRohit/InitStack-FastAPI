# Third-Party Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

from config.mailer import render_template, send_email

# Local Imports
from config.mongodb import get_mongodb
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User, UserResponse


# Internal Function to Send Activated Email
async def _send_activated_email(user: User, token: str) -> None:
    """
    Send Activated Email

    Args:
        user (User): User Instance
        token (str): Activation Token
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
async def activate_user_hander(token: str) -> JSONResponse:
    """
    Activate User

    Args:
        token (str): Activation Token

    Returns:
        JSONResponse: UserResponse with User Data

    Raises:
        HTTPException: For Validation Errors or Conflicts
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

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        jwt.InvalidAudienceError,
        jwt.InvalidIssuerError,
        jwt.InvalidSignatureError,
    ):
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
    async with get_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Get User by ID
        user_doc: dict | None = await mongo_collection.find_one(
            filter={
                "_id": payload["sub"],
            },
        )

        # If User Not Found
        if not user_doc:
            # Return Not Found Response
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User Not Found"},
            )

        # If User Already Activated
        if user_doc["is_active"]:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "User Already Activated"},
            )

        # Update User in Database
        response = await mongo_collection.update_one(
            filter={
                "_id": payload["sub"],
            },
            update={
                "$set": {
                    "is_active": True,
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

        # Update user_doc with activated status
        user_doc["is_active"] = True

    # Create User instance
    user: User = User(**user_doc)

    # Send Activated Email
    await _send_activated_email(user=user, token=stored_token)

    # Prepare Response Data
    response_data: dict = {key: value for key, value in user.model_dump().items() if key != "password"}

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["activate_user_hander"]
