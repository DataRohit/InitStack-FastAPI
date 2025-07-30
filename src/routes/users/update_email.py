# Standard Library Imports
import datetime
from pathlib import Path
from typing import Annotated

# Third-Party Imports
import jwt
from fastapi import Depends, status
from fastapi.responses import JSONResponse

# Local Imports
from config.jwt_auth import get_current_user
from config.mailer import render_template, send_email
from config.redis_cache import get_async_redis
from config.settings import settings
from src.models.users import User
from src.models.users.update_email import UserUpdateEmailRequest
from src.routes.users.base import router


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


# User Update Email Endpoint
@router.post(
    path="/update_email",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate User Email Update",
    description="""
    Initiate User Email Update.

    This Endpoint Allows an Authenticated User to Initiate an Email Update:
    - Requires Valid JWT Authentication
    - Sends a Confirmation Email to the User's Current Email Address
    """,
    name="Update Email",
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Email Update Initiated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Email Update Initiated": {
                            "summary": "Email Update Initiated",
                            "value": {
                                "message": "Email Update Initiated. Check Your Email For Confirmation.",
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
                        "Invalid Credentials": {
                            "summary": "Invalid Credentials",
                            "value": {
                                "detail": "Invalid Authentication Credentials",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "examples": {
                        "Authentication Required": {
                            "summary": "Authentication Required",
                            "value": {
                                "detail": "Authentication Required",
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
                        "Invalid Email Format": {
                            "summary": "Invalid Email Format",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "new_email",
                                        "reason": "Invalid Email Format",
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
                                "detail": "Failed To Initiate Email Update",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_email(
    request: UserUpdateEmailRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """
    Initiate User Email Update.

    Args:
        request (UserUpdateEmailRequest): UserUpdateEmailRequest Containing New Email
        current_user (User): The Authenticated User From Dependency

    Returns:
        JSONResponse: Success Message With 202 Status
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
__all__: list[str] = ["update_email"]
