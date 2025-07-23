# Standard Library Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse

# Local Imports
from config.mailer import render_template, send_email
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User


# Internal Function to Generate Deactivation Token
async def _generate_deactivation_token(
    user: User,
    current_time: datetime.datetime,
    expiry_time: datetime.timedelta,
) -> str:
    """
    Generate Deactivation Token

    Args:
        user (User): User Instance
        current_time (datetime.datetime): Current Time
        expiry_time (datetime.timedelta): Expiry Time

    Returns:
        str: Deactivation Token
    """

    # Generate Deactivation Token
    deactivation_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.DEACTIVATE_JWT_SECRET,
        algorithm=settings.DEACTIVATE_JWT_ALGORITHM,
    )

    # Set Deactivation Token in Redis
    await redis_manager.set(
        key=f"deactivation_token:{user.id}",
        value=deactivation_token,
        expire=settings.DEACTIVATE_JWT_EXPIRE,
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

    # Return Deactivation Token
    return deactivation_token


# Internal Function to Send Deactivation Email
async def _send_deactivation_email(user: User) -> None:
    """
    Send Deactivation Email

    Args:
        user (User): User Instance
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.DEACTIVATE_JWT_EXPIRE)

    # Get Token from Redis
    stored_token: str | None = await redis_manager.get(
        key=f"deactivation_token:{user.id}",
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

    # If Token Not Found
    if not stored_token:
        # Generate Deactivation Token
        deactivation_token: str = await _generate_deactivation_token(
            user=user,
            current_time=current_time,
            expiry_time=expiry_time,
        )

    else:
        try:
            # Decode Token
            jwt.decode(
                jwt=stored_token,
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

            # Set Deactivation Token
            deactivation_token: str = stored_token

        except jwt.InvalidTokenError:
            # Generate New Deactivation Token
            deactivation_token: str = await _generate_deactivation_token(
                user=user,
                current_time=current_time,
                expiry_time=expiry_time,
            )

    # Create Deactivation Link
    deactivation_link: str = f"{settings.PROJECT_DOMAIN}/api/users/deactivate_confirm?token={deactivation_token}"

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "deactivation_link": deactivation_link,
        "deactivation_link_expiry": expiry_time.isoformat(),
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "deactivate.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject=f"Deactivate Your {settings.PROJECT_NAME} Account",
        html_content=html_content,
    )


# Initiate User Deactivation
async def deactivate_user_handler(current_user: User) -> JSONResponse:
    """
    Initiate User Deactivation

    Generates a deactivation token and sends a confirmation email to the user.

    Args:
        current_user (User): The authenticated user from dependency

    Returns:
        JSONResponse: Success message with 202 status
    """

    # If User Already Deactivated
    if not current_user.is_active:
        # Return Conflict Response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User Already Deactivated"},
        )

    # Send Deactivation Email
    await _send_deactivation_email(user=current_user)

    # Return Success Response
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"detail": "User Deactivation Email Sent Successfully"},
    )


# Exports
__all__: list[str] = ["deactivate_user_handler"]
