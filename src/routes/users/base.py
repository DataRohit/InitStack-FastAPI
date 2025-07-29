# Standard Library Imports
from typing import Annotated

# Third-Party Imports
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

# Local Imports
from config.jwt_auth import get_current_user
from src.models.users import User, UserCheckUsernameRequest, UserRegisterRequest, UserResponse
from src.models.users.login import UserLoginRequest, UserLoginResponse
from src.models.users.reset_password import UserResetPasswordRequest
from src.models.users.reset_password_confirm import UserResetPasswordConfirmRequest
from src.models.users.update_username_confirm import UserUpdateUsernameConfirmRequest
from src.routes.users.activate import activate_user_handler
from src.routes.users.check_username import check_username_handler
from src.routes.users.deactivate import deactivate_user_handler
from src.routes.users.deactivate_confirm import deactivate_user_confirm_handler
from src.routes.users.delete import delete_user_handler
from src.routes.users.delete_confirm import delete_user_confirm_handler
from src.routes.users.login import login_user_handler
from src.routes.users.me import get_current_user_handler
from src.routes.users.register import register_user_handler
from src.routes.users.reset_password import reset_password_handler
from src.routes.users.reset_password_confirm import reset_password_confirm_handler
from src.routes.users.update_username import update_username_handler
from src.routes.users.update_username_confirm import update_username_confirm_handler

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
                    "examples": {
                        "Successful Activation": {
                            "summary": "Successful Activation",
                            "value": {
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
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Activation Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Activation Token",
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
                        "Already Activated": {
                            "summary": "Already Activated",
                            "value": {
                                "detail": "User Already Activated",
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
                        "Missing Token": {
                            "summary": "Missing Token",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "token",
                                        "reason": "Field Required",
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
                        "Activation Failed": {
                            "summary": "Activation Failed",
                            "value": {
                                "detail": "Failed to Activate User",
                            },
                        },
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
                    "examples": {
                        "Successful Login": {
                            "summary": "Successful Login",
                            "value": {
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
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Missing Identifier": {
                            "summary": "Missing Identifier",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "type": "missing",
                                        "loc": ["body", "identifier"],
                                        "msg": "Field Required",
                                        "input": None,
                                    },
                                ],
                            },
                        },
                        "Missing Password": {
                            "summary": "Missing Password",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "type": "missing",
                                        "loc": ["body", "password"],
                                        "msg": "Field Required",
                                        "input": None,
                                    },
                                ],
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
                        "Invalid Password": {
                            "summary": "Invalid Password",
                            "value": {
                                "detail": "Invalid Password",
                            },
                        },
                        "Account Not Activated": {
                            "summary": "Account Not Activated",
                            "value": {
                                "detail": "User Account Has Not Been Activated",
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
    },
)
async def login_user(request: UserLoginRequest) -> JSONResponse:
    """
    Login User

    Args:
        request (UserLoginRequest): UserLoginRequest Containing User Login Data

    Returns:
        JSONResponse: UserLoginResponse with User Data
    """

    # Login User
    return await login_user_handler(request=request)


# User Me Endpoint
@router.get(
    path="/me",
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="""
    Returns The Currently Authenticated User's Data.

    This Endpoint Allows a User to Retrieve Their Own Data:
    - Requires Valid JWT Authentication
    """,
    name="Current User",
    response_model=UserResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "User Data Retrieved Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Active User": {
                            "summary": "Active User",
                            "value": {
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
                    },
                },
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Retrieval Failed": {
                            "summary": "Retrieval Failed",
                            "value": {
                                "detail": "Failed To Get Current User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def get_current_user_route(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Returns The Currently Authenticated User's Data.

    Args:
        current_user (User): The Authenticated User From Dependency

    Returns:
        JSONResponse: User Data With 200 Status
    """

    # Get Current User
    return get_current_user_handler(current_user=current_user)


# User Deactivate Endpoint
@router.get(
    path="/deactivate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="User Deactivate Endpoint",
    description="""
    Initiates User Deactivation Process.

    This Endpoint Allows a User to Initiate the Deactivation Process by Providing:
    - Requires Valid JWT Authentication
    """,
    name="User Deactivate",
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "User Deactivation Email Sent Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Deactivation Email Sent": {
                            "summary": "Deactivation Email Sent",
                            "value": {
                                "detail": "User Deactivation Email Sent Successfully",
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
                        "Already Deactivated": {
                            "summary": "Already Deactivated",
                            "value": {
                                "detail": "User Already Deactivated",
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
                        "Deactivation Failed": {
                            "summary": "Deactivation Failed",
                            "value": {
                                "detail": "Failed To Deactivate User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def deactivate_user_route(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Deactivates The Currently Authenticated User's Account.

    Args:
        current_user (User): The Authenticated User From Dependency

    Returns:
        JSONResponse: Success Message With 202 Status
    """

    # Deactivate User
    return await deactivate_user_handler(current_user=current_user)


# User Delete Endpoint
@router.get(
    path="/delete",
    status_code=status.HTTP_202_ACCEPTED,
    summary="User Delete Endpoint",
    description="""
    Initiates User Delete Process.

    This Endpoint Allows a User to Initiate the Delete Process by Providing:
    - Requires Valid JWT Authentication
    """,
    name="User Delete",
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "User Delete Email Sent Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Delete Email Sent": {
                            "summary": "Delete Email Sent",
                            "value": {
                                "detail": "User Delete Email Sent Successfully",
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
                        "User Not Active": {
                            "summary": "User Not Active",
                            "value": {
                                "detail": "User Is Not Active",
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
                        "Delete Failed": {
                            "summary": "Delete Failed",
                            "value": {
                                "detail": "Failed To Delete User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def delete_user_route(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Deletes The Currently Authenticated User's Account.

    Args:
        current_user (User): The Authenticated User From Dependency

    Returns:
        JSONResponse: Success Message With 202 Status
    """

    # Delete User
    return await delete_user_handler(current_user=current_user)


# User Deactivate Confirm Endpoint
@router.get(
    path="/deactivate_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Deactivate Confirm Endpoint",
    description="""
    Confirms User Deactivation Process.

    This Endpoint Allows a User to Confirm the Deactivation Process by Providing:
    - Deactivation Token (Query Parameter)
    """,
    name="User Deactivate Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "User Deactivated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Successful Deactivation": {
                            "summary": "Successful Deactivation",
                            "value": {
                                "detail": "User Deactivated Successfully",
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
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Deactivation Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Deactivation Token",
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
                        "Already Deactivated": {
                            "summary": "Already Deactivated",
                            "value": {
                                "detail": "User Already Deactivated",
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
                        "Missing Token": {
                            "summary": "Missing Token",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "token",
                                        "reason": "Field Required",
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
                        "Deactivation Failed": {
                            "summary": "Deactivation Failed",
                            "value": {
                                "detail": "Failed To Deactivate User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def deactivate_user_confirm_route(token: str) -> JSONResponse:
    """
    Confirms User Deactivation Process.

    Args:
        token (str): Deactivation Token

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    # Deactivate User
    return await deactivate_user_confirm_handler(token=token)


# User Delete Confirm Endpoint
@router.get(
    path="/delete_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Delete Confirm Endpoint",
    description="""
    Confirms User Deletion Process.

    This Endpoint Allows a User to Confirm Account Deletion by Providing:
    - Valid Deletion Token
    """,
    name="User Delete Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "User Deleted Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Successfully Deleted": {
                            "summary": "Successfully Deleted",
                            "value": {
                                "detail": "User Deleted Successfully",
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
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Deletion Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Deletion Token",
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
                        "User Not Active": {
                            "summary": "User Not Active",
                            "value": {
                                "detail": "User Is Not Active",
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
                        "Deletion Failed": {
                            "summary": "Deletion Failed",
                            "value": {
                                "detail": "Failed To Delete User",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def delete_user_confirm_route(token: str) -> JSONResponse:
    """
    Confirms User Deletion Process.

    Args:
        token (str): Deletion Token

    Returns:
        JSONResponse: Success Message With 200 Status
    """
    return await delete_user_confirm_handler(token=token)


# User Reset Password Endpoint
@router.post(
    path="/reset_password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="User Reset Password Endpoint",
    description="""
    Initiate User Reset Password Process.

    This Endpoint Allows a User to Initiate the Reset Password Process by Providing:
    - Identifier (Username or Email)

    Returns:
        JSONResponse: Success Message With 202 Status
    """,
    name="User Reset Password",
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Reset Password Email Sent Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Email Sent": {
                            "summary": "Email Sent",
                            "value": {
                                "detail": "User Reset Password Email Sent Successfully",
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
                    },
                },
            },
        },
    },
)
async def reset_password_route(request: UserResetPasswordRequest) -> JSONResponse:
    """
    Initiate Reset Password Process.

    Args:
        request (UserResetPasswordRequest): Reset Password Request

    Returns:
        JSONResponse: Success Message With 202 Status
    """

    # Reset Password
    return await reset_password_handler(request=request)


# User Reset Password Confirm Endpoint
@router.post(
    path="/reset_password_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Reset Password Confirm Endpoint",
    description="""
    Confirms User Reset Password Process.

    This Endpoint Allows a User to Confirm the Reset Password Process by Providing:
    - Reset Password Request (Password and Password Confirmation)
    - Reset Password Token (Query Parameter)

    Returns:
        JSONResponse: Success Message With 200 Status
    """,
    name="User Reset Password Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "User Reset Password Confirmed Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Password Reset Confirmed": {
                            "summary": "Password Reset Confirmed",
                            "value": {
                                "detail": "User Reset Password Confirmed Successfully",
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
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Reset Password Token",
                            },
                        },
                        "Token Not Found": {
                            "summary": "Token Not Found",
                            "value": {
                                "detail": "Invalid Reset Password Token",
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
                    },
                },
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Reset Failed": {
                            "summary": "Reset Failed",
                            "value": {
                                "detail": "Failed To Reset Password",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def reset_password_confirm_route(request: UserResetPasswordConfirmRequest, token: str) -> JSONResponse:
    """
    Resets User Password.

    Args:
        request (UserResetPasswordConfirmRequest): Reset Password Confirm Request
        token (str): Reset Password Token

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    # Reset Password Confirm
    return await reset_password_confirm_handler(request=request, token=token)


# User Check Username Endpoint
@router.post(
    path="/check_username",
    status_code=status.HTTP_200_OK,
    summary="Check Username Availability",
    description="""
    Check if a Username is Available.

    This Endpoint Allows Checking if a Given Username is Already Taken by Another User.
    It Returns a Success Response if the Username is Available, or a Conflict Response if it is Already in Use.
    """,
    name="Check Username",
    responses={
        status.HTTP_200_OK: {
            "description": "Username is Available",
            "content": {
                "application/json": {
                    "examples": {
                        "Username Available": {
                            "summary": "Username Available",
                            "value": {"detail": "Username is Available"},
                        },
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Username Already Exists",
            "content": {
                "application/json": {
                    "examples": {
                        "Username Taken": {
                            "summary": "Username Taken",
                            "value": {"detail": "Username Already Exists"},
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
                        "Invalid Username Format": {
                            "summary": "Invalid Username Format",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "username",
                                        "reason": "Username Must Be 8+ Characters, Using Lowercase Letters, Numbers, @, -, _",  # noqa: E501
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
                        "Internal Server Error": {
                            "summary": "Internal Server Error",
                            "value": {
                                "detail": "Internal Server Error",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def check_username(request: UserCheckUsernameRequest) -> JSONResponse:
    """
    Check Username Availability

    Args:
        request (UserCheckUsernameRequest): UserCheckUsernameRequest Containing Username to Check

    Returns:
        JSONResponse: Success or Error Response Indicating Username Availability
    """

    # Check Username Availability
    return await check_username_handler(request=request)


# User Update Username Endpoint
@router.post(
    path="/update_username",
    status_code=status.HTTP_202_ACCEPTED,
    summary="User Update Username Endpoint",
    description="""
    Initiate User Update Username Process.

    This Endpoint Allows an Authenticated User to Initiate the Username Update Process.
    A Confirmation Email Will Be Sent to the User's Registered Email Address.
    """,
    name="User Update Username",
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "User Update Username Email Sent Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Success": {
                            "summary": "Success",
                            "value": {
                                "detail": "User Update Username Email Sent Successfully",
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
                        "Unauthorized": {
                            "summary": "Unauthorized",
                            "value": {
                                "detail": "Not Authenticated",
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
                        "User Not Active": {
                            "summary": "User Not Active",
                            "value": {
                                "detail": "User Account Not Active",
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
                        "Failed to Send Email": {
                            "summary": "Failed to Send Email",
                            "value": {
                                "detail": "Failed to Send Update Username Email",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_username_route(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Initiate User Update Username

    Args:
        current_user (User): The Authenticated User From Dependency

    Returns:
        JSONResponse: Success Message With 202 Status
    """

    # Initiate User Update Username
    return await update_username_handler(current_user=current_user)


# User Update Username Confirm Endpoint
@router.post(
    path="/update_username_confirm",
    status_code=status.HTTP_200_OK,
    summary="User Update Username Confirmation Endpoint",
    description="""
    Confirm User Update Username Process.

    This Endpoint Allows a User to Confirm Their Username Update by Providing:
    - Update Username Token (Query Parameter)
    - New Username (Request Body)
    """,
    name="User Update Username Confirm",
    responses={
        status.HTTP_200_OK: {
            "description": "Username Updated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Success": {
                            "summary": "Success",
                            "value": {
                                "detail": "Username Updated Successfully",
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
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Update Username Token",
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
                        "Username Exists": {
                            "summary": "Username Exists",
                            "value": {
                                "detail": "Username Already Exists",
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
                        "Missing Token": {
                            "summary": "Missing Token",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "token",
                                        "reason": "Field Required",
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
                        "Failed to Update Username": {
                            "summary": "Failed to Update Username",
                            "value": {
                                "detail": "Failed to Update Username",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_username_confirm_route(
    token: str,
    request: UserUpdateUsernameConfirmRequest,
) -> JSONResponse:
    """
    Confirm User Update Username

    Args:
        token (str): Update Username Token
        request (UserUpdateUsernameConfirmRequest): UserUpdateUsernameConfirmRequest Containing New Username

    Returns:
        JSONResponse: Success Message With 200 Status
    """

    # Confirm User Update Username
    return await update_username_confirm_handler(token=token, request=request)


# Exports
__all__: list[str] = ["router"]
