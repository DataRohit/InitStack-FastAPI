# Third-Party Imports
import datetime
import logging

# Third-Party Imports
import jwt
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_mongodb
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User, UserRegisterRequest, UserRegisterResponse, UserResponse

# Create Logger
logger = logging.getLogger(__name__)

# Create Router
router = APIRouter(
    prefix="",
    tags=["Users"],
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
    response_model=UserRegisterResponse,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User Registered Successfully",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": "687ea9fa53bf34da640e4ef5",
                            "username": "john_doe",
                            "email": "john_doe@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "is_active": False,
                            "is_staff": False,
                            "is_superuser": False,
                            "date_joined": "2025-07-21T20:58:34.273678+00:00",
                            "last_login": "2025-07-21T21:58:34.273678+00:00",
                            "updated_at": "2025-07-21T21:30:34.273678+00:00",
                        },
                        "activation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjVkY2Y4YzYwYjI0ZTAwMTFlYjQ4YjQ5IiwiaWF0IjoxNzE4ODQ1NjAwLCJleHAiOjE3MTg5MzIwMDB9.1q3X2Q4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0",  # noqa: E501
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Validation Error",
                        "errors": [
                            {
                                "field": "password",
                                "reason": "Password Must Contain At Least 1 Uppercase Letter, 1 Lowercase Letter, 1 Number & 1 Special Character",  # noqa: E501
                            },
                        ],
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User With This Username or Email Already Exists",
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Invalid Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid Request",
                        "errors": [
                            {
                                "type": "missing",
                                "loc": ["body", "first_name"],
                                "msg": "Field Required",
                                "input": {
                                    "username": "john_doe",
                                    "email": "john_doe@example.com",
                                    "password": "SecurePassword@123",
                                    "last_name": "Doe",
                                },
                            },
                        ],
                    },
                },
            },
        },
    },
)
async def register_user(request: UserRegisterRequest):
    """
    Register a New User

    Args:
        request: UserRegisterRequest containing user registration data

    Returns:
        UserRegisterResponse with user data and activation token

    Raises:
        HTTPException: For validation errors or conflicts
    """

    # Get Database
    async with get_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

    # Check if user already exists
    existing_user: User | None = await User.get_by_identifier(
        collection=mongo_collection,
        identifier=request.username,
    ) or await User.get_by_identifier(
        collection=mongo_collection,
        identifier=request.email,
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
    await user.create(collection=mongo_collection, user_data=user.model_dump(by_alias=True))

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(datetime.UTC)

    # Generate Activation Token
    activation_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": current_time + datetime.timedelta(seconds=settings.ACTIVATION_JWT_EXPIRE),
        },
        key=settings.ACTIVATION_JWT_SECRET,
        algorithm=settings.ACTIVATION_JWT_ALGORITHM,
    )

    # Set Activation Token in Redis
    await redis_manager.set(
        key=f"activation_token:{user.id}",
        value=activation_token,
        expire=settings.ACTIVATION_JWT_EXPIRE,
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

    # Dump User Data
    user_dump: dict = user.model_dump()

    # Remove Password from User Data
    user_dump.pop("password")

    # Return Response with UserResponse Model
    return {
        "user": UserResponse(**user_dump).model_dump(),
        "activation_token": activation_token,
    }
