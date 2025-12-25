# ruff: noqa: TC001, TC003

import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas.auth.me import MeResponse
from src.utils.jwt_auth import get_current_user


def register_me_routes(router: APIRouter, logger: logging.Logger) -> None:
    """Register Me Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.get(
        path="/me",
        response_model=MeResponse,
        status_code=status.HTTP_200_OK,
        summary="Me",
        description="Return the authenticated user's profile.",
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "PostgreSQL is disabled or not available",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "postgresql_disabled": {
                                "summary": "PostgreSQL disabled",
                                "description": "Example response when PostgreSQL is disabled in configuration",
                                "value": {
                                    "error": "PostgreSQL is not enabled in settings",
                                    "detail": "HTTP 503",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Internal server error",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "me_failed": {
                                "summary": "Me failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to get current user",
                                    "detail": "HTTP 500",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_429_TOO_MANY_REQUESTS: {
                "description": "Rate limit exceeded",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "rate_limit_exceeded": {
                                "summary": "Rate limit exceeded",
                                "description": "Example response when client exceeds rate limit",
                                "value": {
                                    "error": "Rate limit exceeded. Try again in 30 seconds.",
                                    "detail": "HTTP 429",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
                "description": "Request entity too large",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "request_too_large": {
                                "summary": "Request too large",
                                "description": "Example response when request exceeds configured size limits",
                                "value": {
                                    "error": "Request size 99999999 bytes exceeds maximum allowed 16777216 bytes",
                                    "detail": "HTTP 413",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Account not active",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "account_not_active": {
                                "summary": "Account not active",
                                "description": "Example response when user account is inactive",
                                "value": {
                                    "error": "Account is not active",
                                    "detail": "HTTP 403",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Unauthorized",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "not_authenticated": {
                                "summary": "Not authenticated",
                                "description": "Example response when Authorization header is missing or empty",
                                "value": {
                                    "error": "Not authenticated",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "invalid_token": {
                                "summary": "Invalid access token",
                                "description": "Example response when access token is invalid or expired",
                                "value": {
                                    "error": "Invalid access token",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "User profile returned successfully",
                "model": MeResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "me_success": {
                                "summary": "Me",
                                "description": "Example response for authenticated user",
                                "value": {
                                    "id": "b2c1f7c6-1e27-4f2e-9b92-27d0f0f7c9a1",
                                    "username": "john_doe",
                                    "email": "user@example.com",
                                    "first_name": "John",
                                    "last_name": "Doe",
                                    "is_active": True,
                                    "is_admin": False,
                                    "is_superuser": False,
                                    "created_at": "2025-01-01T12:34:56Z",
                                    "updated_at": "2025-01-01T12:35:10Z",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def me_endpoint(current_user: Annotated[User, Depends(dependency=get_current_user)]) -> MeResponse:
        """Me Endpoint.

        Arguments:
            current_user (User): Authenticated user.

        Returns:
            MeResponse: Current user profile.

        Raises:
            HTTPException: If request fails.
        """

        try:
            response = MeResponse(
                id=str(object=current_user.id),
                username=current_user.username,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                is_active=current_user.is_active,
                is_admin=current_user.is_admin,
                is_superuser=current_user.is_superuser,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at,
            )

            logger.info(
                msg="Me endpoint called",
                extra={"user_id": str(object=current_user.id), "username": current_user.username},
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Me endpoint failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get current user",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_me_routes"]
