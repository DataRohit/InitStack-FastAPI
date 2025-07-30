# Standard Library Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import InsertOneResult

# Local Imports
from config.mailer import render_template, send_email
from config.mongodb import get_async_mongodb
from config.redis_cache import get_async_redis
from config.settings import settings
from src.models.users import User, UserRegisterRequest, UserResponse
from src.routes.users.base import router


# Internal Function to Send Activation Email
async def _send_activation_email(user: User) -> None:
    """
    Send Activation Email

    Args:
        user (User): User Instance
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.ACTIVATION_JWT_EXPIRE)

    # Generate Activation Token
    activation_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.ACTIVATION_JWT_SECRET,
        algorithm=settings.ACTIVATION_JWT_ALGORITHM,
    )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Set Activation Token in Redis
        await redis.set(
            f"activation_token:{user.id}",
            value=activation_token,
            ex=settings.ACTIVATION_JWT_EXPIRE,
        )

    # Create Activation Link
    activation_link: str = f"{settings.PROJECT_DOMAIN}/api/users/activate?token={activation_token}"

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "activation_link": activation_link,
        "activation_link_expiry": expiry_time.isoformat(),
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "registered.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject=f"Activate Your {settings.PROJECT_NAME} Account",
        html_content=html_content,
    )


# User Register Endpoint
@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="User Registration Endpoint",
    description="""
    Register a New User.

    This Endpoint Allows a New User to Register by Providing:
    - Username (3-30 Chars, Lowercase Alphanumeric with @-_)
    - Email (Valid Format)
    - Password (Min 8 Chars, Requires Uppercase, Lowercase, Number, Special Char)
    - First Name (3-30 Chars, Letters Only)
    - Last Name (3-30 Chars, Letters Only)
    """,
    name="User Register",
    response_model=UserResponse,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User Registered Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "New User": {
                            "summary": "New User",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "username": "john_doe",
                                "email": "john_doe@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "is_active": False,
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
        status.HTTP_400_BAD_REQUEST: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Password": {
                            "summary": "Invalid Password",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "password",
                                        "reason": "Password Must Contain At Least 1 Uppercase Letter, 1 Lowercase Letter, 1 Number & 1 Special Character",  # noqa: E501
                                    },
                                ],
                            },
                        },
                        "Invalid Email": {
                            "summary": "Invalid Email",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "email",
                                        "reason": "Invalid Email Format",
                                    },
                                ],
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
                        "Duplicate User": {
                            "summary": "Duplicate User",
                            "value": {
                                "detail": "User With This Username or Email Already Exists",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid Request",
            "content": {
                "application/json": {
                    "examples": {
                        "Missing First Name": {
                            "summary": "Missing First Name",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "first_name",
                                        "reason": "Field Required",
                                    },
                                ],
                            },
                        },
                        "Password Mismatch": {
                            "summary": "Password Mismatch",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "confirm_password",
                                        "reason": "Passwords Do Not Match",
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
                        "Registration Failed": {
                            "summary": "Registration Failed",
                            "value": {
                                "detail": "Failed to Register User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def register_user(request: UserRegisterRequest) -> JSONResponse:
    """
    Register a New User

    Args:
        request (UserRegisterRequest): UserRegisterRequest Containing User Registration Data

    Returns:
        JSONResponse: UserResponse with User Data
    """
    """
    Register a New User

    Args:
        request (UserRegisterRequest): UserRegisterRequest Containing User Registration Data

    Returns:
        JSONResponse: UserResponse with User Data
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Check If User Already Exists
        existing_user: dict | None = await mongo_collection.find_one(
            filter={
                "$or": [
                    {"username": request.username},
                    {"email": request.email},
                ],
            },
        )

        # If User Already Exists
        if existing_user:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "User With This Username or Email Already Exists"},
            )

        # Create and Validate User
        user: User = User(
            username=request.username,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password,
        )

        # This Will Validate Password Complexity and Hash It
        user.set_password(password=request.password)

        # Save to Database
        result: InsertOneResult | None = await mongo_collection.insert_one(
            document=user.model_dump(by_alias=True),
        )

    # If Insertion Failed
    if not result:
        # Return Internal Server Error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to Register User"},
        )

    # Send Activation Email
    await _send_activation_email(user=user)

    # Prepare Response Data
    response_data: dict = {key: value for key, value in user.model_dump().items() if key != "password"}

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=UserResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["register_user"]
