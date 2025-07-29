# Standard Library Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse

# Local Imports
from config.mailer import render_template, send_email
from config.redis_cache import get_async_redis
from config.settings import settings
from src.models.users import User


# Internal Function to Generate Update Username Token
async def _generate_update_username_token(
    user: User,
    current_time: datetime.datetime,
    expiry_time: datetime.timedelta,
) -> str:
    """
    Generate Update Username Token

    Args:
        user (User): User Instance
        current_time (datetime.datetime): Current Time
        expiry_time (datetime.timedelta): Expiry Time

    Returns:
        str: Update Username Token
    """

    # Generate Update Username Token
    update_username_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.UPDATE_USERNAME_JWT_SECRET,
        algorithm=settings.UPDATE_USERNAME_JWT_ALGORITHM,
    )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Set Update Username Token in Redis
        await redis.set(f"update_username_token:{user.id}", value=update_username_token)

    # Return Update Username Token
    return update_username_token


# Internal Function to Send Update Username Email
async def _send_update_username_email(user: User) -> None:
    """
    Send Update Username Email

    Args:
        user (User): User Instance
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.UPDATE_USERNAME_JWT_EXPIRE)

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get(f"update_username_token:{user.id}")

    # If Token Not Found
    if not stored_token:
        # Generate Update Username Token
        update_username_token: str = await _generate_update_username_token(
            user=user,
            current_time=current_time,
            expiry_time=expiry_time,
        )

    else:
        try:
            # Decode Token
            jwt.decode(
                jwt=stored_token,
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

            # Set Update Username Token
            update_username_token: str = stored_token

        except jwt.InvalidTokenError:
            # Generate New Update Username Token
            update_username_token: str = await _generate_update_username_token(
                user=user,
                current_time=current_time,
                expiry_time=expiry_time,
            )

    # Create Update Username Link
    update_username_link: str = (
        f"{settings.PROJECT_DOMAIN}/api/users/update_username_confirm?token={update_username_token}"
    )

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "update_username_link": update_username_link,
        "update_username_link_expiry": expiry_time.isoformat(),
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "update_username.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject=f"Update Your {settings.PROJECT_NAME} Username",
        html_content=html_content,
    )


# Initiate User Update Username
async def update_username_handler(current_user: User) -> JSONResponse:
    """
    Initiate User Update Username

    Generates an update username token and sends a confirmation email to the user.

    Args:
        current_user (User): The authenticated user from dependency

    Returns:
        JSONResponse: Success message with 202 status
    """

    # If User Not Active
    if not current_user.is_active:
        # Return Conflict Response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User Account Not Active"},
        )

    # Send Update Username Email
    await _send_update_username_email(user=current_user)

    # Return Success Response
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"detail": "User Update Username Email Sent Successfully"},
    )


# Exports
__all__: list[str] = ["update_username_handler"]
