# Standard Library Imports
from typing import Annotated

# Third-Party Imports
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

# Local Imports
from config.jwt_auth import get_current_user
from src.models.profiles import ProfileCreateRequest, ProfileResponse, ProfileUpdateRequest
from src.models.users.base import User
from src.routes.profiles.create import create_profile_handler
from src.routes.profiles.delete import delete_profile_handler
from src.routes.profiles.read import read_profile_handler
from src.routes.profiles.update import update_profile_handler

# Initialize Router
router = APIRouter(
    prefix="/users/profiles",
    tags=["Profiles"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
)


# Create Profile Endpoint
@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    summary="Create Profile Endpoint",
    description="""
    Create a New User Profile.

    This Endpoint Allows a Logged-in User to Create Their Profile by Providing:
    - bio (Optional)
    - phone_number (Optional)
    - date_of_birth (Optional)
    - gender (Optional)
    - country (Optional)
    - city (Optional)
    - timezone (Optional)
    """,
    name="Create Profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Profile Created Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "New Profile": {
                            "summary": "New Profile",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "user_id": "687ea9fa53bf34da640e4ef5",
                                "bio": "Software developer and open source enthusiast",
                                "phone_number": "+1234567890",
                                "date_of_birth": "1990-01-01",
                                "gender": "male",
                                "avatar_url": "http://localhost:8080/dicebear/9.x/avataaars/png?seed=admin&accessories=&eyebrows=default%2CdefaultNatural&eyes=default%2Chappy%2Cwink&mouth=default%2Csmile",
                                "country": "United States",
                                "city": "New York",
                                "timezone": "America/New_York",
                                "created_at": "2025-07-21T20:58:34.273000+00:00",
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
        status.HTTP_409_CONFLICT: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Exists": {
                            "summary": "Profile Already Exists",
                            "value": {
                                "detail": "Profile Already Exists",
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
                        "Invalid Phone Number": {
                            "summary": "Invalid Phone Number",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "phone_number",
                                        "reason": "Phone Number Must Be Between 7 and 15 Digits",
                                    },
                                ],
                            },
                        },
                        "Invalid Date of Birth": {
                            "summary": "Invalid Date of Birth",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "date_of_birth",
                                        "reason": "Date of Birth Cannot Be in the Future",
                                    },
                                ],
                            },
                        },
                        "Invalid Gender": {
                            "summary": "Invalid Gender",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "gender",
                                        "reason": "Gender Must Be One of: male, female, non-binary, other",
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
                        "Creation Failed": {
                            "summary": "Profile Creation Failed",
                            "value": {
                                "detail": "Failed to Create Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def create_profile(
    request: ProfileCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """
    Create Profile

    Args:
        request (ProfileCreateRequest): ProfileCreateRequest Containing Profile Data
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: ProfileResponse with Profile Data
    """

    # Create Profile
    return await create_profile_handler(request=request, current_user=current_user)


# Read Profile Endpoint
@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Read Profile Endpoint",
    description="""
    Read User Profile.

    This Endpoint Allows a Logged-in User to Read Their Profile.
    """,
    name="Read Profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Profile Read Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Data": {
                            "summary": "Profile Data",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "user_id": "687ea9fa53bf34da640e4ef5",
                                "bio": "Software developer and open source enthusiast",
                                "phone_number": "+1234567890",
                                "date_of_birth": "1990-01-01",
                                "gender": "male",
                                "avatar_url": "http://localhost:8080/dicebear/9.x/avataaars/png?seed=admin&accessories=&eyebrows=default%2CdefaultNatural&eyes=default%2Chappy%2Cwink&mouth=default%2Csmile",
                                "country": "United States",
                                "city": "New York",
                                "timezone": "America/New_York",
                                "created_at": "2025-07-21T20:58:34.273000+00:00",
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
                        "Profile Not Found": {
                            "summary": "Profile Not Found",
                            "value": {
                                "detail": "Profile Not Found",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def read_profile(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Read Profile

    Args:
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: ProfileResponse with Profile Data
    """

    # Read Profile
    return await read_profile_handler(current_user=current_user)


# Update Profile Endpoint
@router.put(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Update Profile Endpoint",
    description="""
    Update User Profile.

    This Endpoint Allows a Logged-in User to Update Their Profile by Providing:
    - bio (Optional)
    - phone_number (Optional)
    - date_of_birth (Optional)
    - gender (Optional)
    - country (Optional)
    - city (Optional)
    - timezone (Optional)
    """,
    name="Update Profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Profile Updated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Updated Profile": {
                            "summary": "Updated Profile",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "user_id": "687ea9fa53bf34da640e4ef5",
                                "bio": "Software developer and open source enthusiast",
                                "phone_number": "+1234567890",
                                "date_of_birth": "1990-01-01",
                                "gender": "male",
                                "avatar_url": "http://localhost:8080/dicebear/9.x/avataaars/png?seed=admin&accessories=&eyebrows=default%2CdefaultNatural&eyes=default%2Chappy%2Cwink&mouth=default%2Csmile",
                                "country": "United States",
                                "city": "New York",
                                "timezone": "America/New_York",
                                "created_at": "2025-07-21T20:58:34.273000+00:00",
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
                        "Profile Not Found": {
                            "summary": "Profile Not Found",
                            "value": {
                                "detail": "Profile Not Found",
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
                        "Invalid Phone Number": {
                            "summary": "Invalid Phone Number",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "phone_number",
                                        "reason": "Phone Number Must Be Between 7 and 15 Digits",
                                    },
                                ],
                            },
                        },
                        "Invalid Date of Birth": {
                            "summary": "Invalid Date of Birth",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "date_of_birth",
                                        "reason": "Date of Birth Cannot Be in the Future",
                                    },
                                ],
                            },
                        },
                        "Invalid Gender": {
                            "summary": "Invalid Gender",
                            "value": {
                                "detail": "Validation Error",
                                "errors": [
                                    {
                                        "field": "gender",
                                        "reason": "Gender Must Be One of: male, female, non-binary, other",
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
                        "Update Failed": {
                            "summary": "Profile Update Failed",
                            "value": {
                                "detail": "Failed to Update Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """
    Update Profile

    Args:
        request (ProfileUpdateRequest): ProfileUpdateRequest Containing Profile Data
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: ProfileResponse with Profile Data
    """

    # Update Profile
    return await update_profile_handler(request=request, current_user=current_user)


# Delete Profile Endpoint
@router.delete(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Delete Profile Endpoint",
    description="""
    Delete User Profile.

    This Endpoint Allows a Logged-in User to Delete Their Profile.
    """,
    name="Delete Profile",
    responses={
        status.HTTP_200_OK: {
            "description": "Profile Deleted Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Deleted": {
                            "summary": "Profile Deleted Successfully",
                            "value": {
                                "detail": "Profile Deleted Successfully",
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
                        "Profile Not Found": {
                            "summary": "Profile Not Found",
                            "value": {
                                "detail": "Profile Not Found",
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
                            "summary": "Profile Deletion Failed",
                            "value": {
                                "detail": "Failed to Delete Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def delete_profile(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Delete Profile

    Args:
        current_user (User): Current Authenticated User

    Returns:
        JSONResponse: Confirmation of Profile Deletion
    """

    # Delete Profile
    return await delete_profile_handler(current_user=current_user)


# Exports
__all__: list[str] = [
    "router",
]
