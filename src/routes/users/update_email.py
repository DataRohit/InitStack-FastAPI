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
from src.models.users.update_email import UserUpdateEmailRequest


# Internal Function to Generate Update Email Token
async def _generate_update_email_token(
    user: User,
    new_email: str,
    current_time: datetime.datetime,
    expiry_time: datetime.timedelta,
) -> str:
    """
    Generate Update Email Token

    Args:
        user (User): User Instance
        new_email (str): The New Email Address
        current_time (datetime.datetime): Current Time
        expiry_time (datetime.timedelta): Expiry Time

    Returns:
        str: Update Email Token
    """

    # Generate Update Email Token
    update_email_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "new_email": new_email,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.UPDATE_EMAIL_JWT_SECRET,
        algorithm=settings.UPDATE_EMAIL_JWT_ALGORITHM,
    )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Set Update Email Token in Redis
        await redis.set(f"update_email_token:{user.id}", value=update_email_token)

    # Return Update Email Token
    return update_email_token


# Internal Function to Send Update Email
async def _send_update_email(
    user: User,
    request: UserUpdateEmailRequest,
) -> None:
    """
    Send Update Email

    Args:
        user (User): User Instance
        request (UserUpdateEmailRequest): UserUpdateEmailRequest Containing New Email
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.UPDATE_EMAIL_JWT_EXPIRE)

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Token from Redis
        stored_token: str | None = await redis.get(f"update_email_token:{user.id}")

    # If Token Not Found
    if not stored_token:
        # Generate Update Email Token
        update_email_token: str = await _generate_update_email_token(
            user=user,
            new_email=request.email,
            current_time=current_time,
            expiry_time=expiry_time,
        )

    else:
        try:
            # Decode Token
            jwt.decode(
                jwt=stored_token,
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

            # Set Update Email Token
            update_email_token: str = stored_token

        except jwt.InvalidTokenError:
            # Generate New Update Email Token
            update_email_token: str = await _generate_update_email_token(
                user=user,
                new_email=request.email,
                current_time=current_time,
                expiry_time=expiry_time,
            )

    # Create Update Email Link
    update_email_link: str = f"{settings.PROJECT_DOMAIN}/api/users/update_email_confirm?token={update_email_token}"

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "new_email": request.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "update_email_link": update_email_link,
        "update_email_link_expiry": expiry_time.isoformat(),
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "update_email.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject=f"Update Your {settings.PROJECT_NAME} Email Address",
        html_content=html_content,
    )


# Initiate User Update Email
async def update_email_handler(
    current_user: User,
    request: UserUpdateEmailRequest,
) -> JSONResponse:
    """
    Initiate User Update Email

    Generates an update email token and sends a confirmation email to the user.

    Args:
        current_user (User): The authenticated user from dependency
        request (UserUpdateEmailRequest): UserUpdateEmailRequest Containing New Email

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

    # Send Update Email
    await _send_update_email(user=current_user, request=request)

    # Return Success Response
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"detail": "User Update Email Sent Successfully"},
    )


# Exports
__all__: list[str] = ["update_email_handler"]
