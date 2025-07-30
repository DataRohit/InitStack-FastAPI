# Standard Library Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mailer import render_template, send_email
from config.mongodb import get_async_mongodb
from config.redis_cache import get_async_redis
from config.settings import settings
from src.models.users import User, UserResetPasswordRequest


# Internal Function to Generate Reset Password Token
async def _generate_reset_password_token(
    user: User,
    current_time: datetime.datetime,
    expiry_time: datetime.timedelta,
) -> str:
    """
    Generate Reset Password Token

    Args:
        user (User): User Instance
        current_time (datetime.datetime): Current Time
        expiry_time (datetime.timedelta): Expiry Time

    Returns:
        str: Reset Password Token
    """

    # Generate Reset Password Token
    reset_password_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.RESET_PASSWORD_JWT_SECRET,
        algorithm=settings.RESET_PASSWORD_JWT_ALGORITHM,
    )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Set Reset Password Token in Redis
        await redis.set(
            f"reset_password_token:{user.id}",
            value=reset_password_token,
            ex=settings.RESET_PASSWORD_JWT_EXPIRE,
        )

    # Return Reset Password Token
    return reset_password_token


# Internal Function to Send Reset Password Email
async def _send_reset_password_email(user: User) -> None:
    """
    Send Reset Password Email

    Args:
        user (User): User Instance
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.RESET_PASSWORD_JWT_EXPIRE)

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Reset Password Token from Redis
        stored_token: str | None = await redis.get(f"reset_password_token:{user.id}")

    # If Token Not Found
    if not stored_token:
        # Generate Reset Password Token
        reset_password_token: str = await _generate_reset_password_token(
            user=user,
            current_time=current_time,
            expiry_time=expiry_time,
        )

    else:
        try:
            # Decode Token
            jwt.decode(
                jwt=stored_token,
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

            # Set Reset Password Token
            reset_password_token: str = stored_token

        except jwt.InvalidTokenError:
            # Generate New Reset Password Token
            reset_password_token: str = await _generate_reset_password_token(
                user=user,
                current_time=current_time,
                expiry_time=expiry_time,
            )

    # Create Reset Password Link
    reset_password_link: str = (
        f"{settings.PROJECT_DOMAIN}/api/users/reset_password_confirm?token={reset_password_token}"
    )

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "reset_password_link": reset_password_link,
        "reset_password_link_expiry": expiry_time.isoformat(),
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "reset_password.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject=f"Reset Your {settings.PROJECT_NAME} Password",
        html_content=html_content,
    )


# Initiate Reset Password
async def reset_password_handler(request: UserResetPasswordRequest) -> JSONResponse:
    """
    Initiate Reset Password

    Args:
        request (UserResetPasswordRequest): Reset Password Request

    Returns:
        JSONResponse: JSON Response
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Get User by Username or Email
        existing_user: dict | None = await mongo_collection.find_one(
            filter={
                "$or": [
                    {"username": request.identifier},
                    {"email": request.identifier},
                ],
            },
        )

    # If User Does Not Exist
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

    # Create User Instance
    user: User = User(**existing_user)

    # Send Reset Password Email
    await _send_reset_password_email(user=user)

    # Return Success Response
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"detail": "User Reset Password Email Sent Successfully"},
    )


# Exports
__all__: list[str] = ["reset_password_handler"]
