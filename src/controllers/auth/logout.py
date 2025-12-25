# ruff: noqa: TC001, TC003

import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas.auth import LogoutResponse
from src.utils.auth_tokens import revoke_login_tokens
from src.utils.jwt_auth import get_current_user


def register_logout_routes(router: APIRouter, logger: logging.Logger) -> None:
    """Register Logout Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.post(
        path="/logout",
        response_model=LogoutResponse,
        status_code=status.HTTP_200_OK,
        summary="Logout",
        description="Logout and revoke access and refresh tokens.",
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "PostgreSQL or Redis is disabled or not available",
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
                            "redis_disabled": {
                                "summary": "Redis disabled",
                                "description": "Example response when Redis is disabled in configuration",
                                "value": {
                                    "error": "Redis is not enabled in settings",
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
                            "logout_failed": {
                                "summary": "Logout failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to logout",
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
                "description": "Logged out successfully",
                "model": LogoutResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "logout_success": {
                                "summary": "Logout successful",
                                "description": "Example successful logout response",
                                "value": {
                                    "message": "Logged out successfully",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def logout_endpoint(current_user: Annotated[User, Depends(dependency=get_current_user)]) -> LogoutResponse:
        """Logout Endpoint.

        Arguments:
            current_user (User): Authenticated user from Authorization header.

        Returns:
            LogoutResponse: Logout response.

        Raises:
            HTTPException: If logout fails.
        """

        try:
            user_id: str = str(object=current_user.id)

            try:
                await revoke_login_tokens(user_id=user_id)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            response = LogoutResponse(message="Logged out successfully")

            logger.info(
                msg="User logged out successfully",
                extra={"user_id": user_id, "username": current_user.username},
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Logout failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_logout_routes"]
