# Third-Party Imports
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

# Local Imports
from src.models.users import UserRegisterRequest, UserResponse
from src.routes.users.register import register_user_hander

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
                        "date_joined": "2025-07-21T20:58:34.273678+00:00",
                        "last_login": "2025-07-21T21:58:34.273678+00:00",
                        "updated_at": "2025-07-21T21:30:34.273678+00:00",
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
async def register_user(request: UserRegisterRequest) -> JSONResponse:
    """
    Register a New User

    Args:
        request: UserRegisterRequest Containing User Registration Data

    Returns:
        JSONResponse: UserResponse with User Data

    Raises:
        HTTPException: For Validation Errors or Conflicts
    """

    # Register User
    return await register_user_hander(request=request)


# Exports
__all__: list[str] = ["router"]
