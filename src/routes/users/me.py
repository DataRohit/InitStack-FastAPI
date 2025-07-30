# Standard Library Imports
from typing import Annotated

# Third-Party Imports
from fastapi import Depends, status
from fastapi.responses import JSONResponse

# Local Imports
from config.jwt_auth import get_current_user
from src.models.users import User, UserResponse
from src.routes.users.base import router


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
async def get_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Returns The Currently Authenticated User's Data.

    Args:
        current_user (User): The Authenticated User From Dependency

    Returns:
        JSONResponse: User Data With 200 Status
    """

    # If User Is Not Active
    if not current_user.is_active:
        # Return Conflict Response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User Is Not Active"},
        )

    # Prepare Response Data
    response_data: dict = {key: value for key, value in current_user.model_dump().items() if key != "password"}

    # Return User Data
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["get_current_user"]
