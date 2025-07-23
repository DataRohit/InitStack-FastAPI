# Third-Party Imports
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# Local Imports
from src.models.users import UserRegisterRequest, UserResponse
from src.models.users.login import UserLoginRequest, UserLoginResponse
from src.routes.users.activate import activate_user_handler
from src.routes.users.login import login_user_handler
from src.routes.users.register import register_user_handler

# Initialize Router
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
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
                    "example": {
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
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to Register User",
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

    Raises:
        HTTPException: For Validation Errors or Conflicts
    """

    # Register User
    return await register_user_handler(request=request)


# User Activate Endpoint
@router.get(
    path="/activate",
    status_code=status.HTTP_200_OK,
    summary="User Activation Endpoint",
    description="""
    Activate a User Account.

    This Endpoint Allows a User to Activate Their Account by Providing:
    - Activation Token (Query Parameter)
    """,
    name="User Activate",
    responses={
        status.HTTP_200_OK: {
            "description": "User Activated Successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "687ea9fa53bf34da640e4ef5",
                        "username": "john_doe",
                        "email": "john_doe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "is_active": True,
                        "is_staff": False,
                        "is_superuser": False,
                        "date_joined": "2025-07-21T20:58:34.273000+00:00",
                        "last_login": "2025-07-21T21:58:34.273000+00:00",
                        "updated_at": "2025-07-21T21:30:34.273000+00:00",
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid Activation Token",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User Not Found",
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Unprocessable Entity",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid Request",
                        "errors": [
                            {
                                "type": "missing",
                                "loc": ["body", "password"],
                                "msg": "Field Required",
                                "input": {"identifier": "john_doe@example.com"},
                            },
                        ],
                    },
                },
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to Activate User",
                    },
                },
            },
        },
    },
)
async def activate_user(token: str) -> JSONResponse:
    """
    Activate User

    Args:
        token (str): Activation Token

    Returns:
        JSONResponse: UserResponse with User Data

    Raises:
        HTTPException: For Validation Errors or Conflicts
    """

    # Activate User
    return await activate_user_handler(token=token)


# User Login Endpoint
@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="User Login Endpoint",
    description="""
    Login a User.

    This Endpoint Allows a User to Login by Providing:
    - Identifier (Email or Username)
    - Password
    """,
    name="User Login",
    response_model=UserLoginResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "User Logged In Successfully",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": "687ea9fa53bf34da640e4ef5",
                            "username": "john_doe",
                            "email": "john_doe@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "is_active": True,
                            "is_staff": False,
                            "is_superuser": False,
                            "date_joined": "2025-07-21T20:58:34.273000+00:00",
                            "last_login": "2025-07-21T21:58:34.273000+00:00",
                            "updated_at": "2025-07-21T21:30:34.273000+00:00",
                        },
                        "access_token": {
                            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmMxMjM0NTY3ODkwMTIzNCIsImlzcyI6IkpvaG4gRG9lIiwiYXVkIjoiSm9obiBEb2UiLCJpYXQiOjE2NzY3ODkwMTIsImV4cCI6MTY3Njc4OTIxMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",  # noqa: E501
                            "type": "bearer",
                            "expires_in": 3600,
                        },
                        "refresh_token": {
                            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmMxMjM0NTY3ODkwMTIzNCIsImlzcyI6IkpvaG4gRG9lIiwiYXVkIjoiSm9obiBEb2UiLCJpYXQiOjE2NzY3ODkwMTIsImV4cCI6MTY3Njc4OTIxMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",  # noqa: E501
                            "expires_in": 86400,
                        },
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
                                "type": "missing",
                                "loc": ["body", "identifier"],
                                "msg": "Field Required",
                                "input": {
                                    "password": "SecurePassword@123",
                                },
                            },
                        ],
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User Is Not Active",
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
                                "loc": ["body", "identifier"],
                                "msg": "Field Required",
                                "input": {
                                    "password": "SecurePassword@123",
                                },
                            },
                        ],
                    },
                },
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to Login User",
                    },
                },
            },
        },
    },
)
async def login_user(request: UserLoginRequest) -> JSONResponse:
    """
    Login User

    Args:
        request (UserLoginRequest): UserLoginRequest Containing User Login Data

    Returns:
        JSONResponse: UserLoginResponse with User Data

    Raises:
        HTTPException: For Validation Errors or Conflicts
    """

    # Login User
    return await login_user_handler(request=request)


# Exports
__all__: list[str] = ["router"]
