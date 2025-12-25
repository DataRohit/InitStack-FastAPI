# ruff: noqa: TC002, TC003

import logging
import uuid

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas import ValidationErrorResponse
from src.schemas.auth.relogin import ReloginRequest
from src.schemas.auth.relogin import ReloginResponse
from src.utils.auth_tokens import get_or_create_relogin_tokens
from src.utils.auth_tokens import validate_refresh_token


def register_relogin_routes(router: APIRouter, logger: logging.Logger) -> None:  # noqa: C901
    """Register Relogin Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.post(
        path="/relogin",
        response_model=ReloginResponse,
        status_code=status.HTTP_200_OK,
        summary="Relogin",
        description="Refresh a user session using a refresh token.",
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
                            "relogin_failed": {
                                "summary": "Relogin failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to relogin",
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
            status.HTTP_422_UNPROCESSABLE_ENTITY: {
                "description": "Validation error",
                "model": ValidationErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "missing_required_field": {
                                "summary": "Missing required field",
                                "description": "Example response when refresh_token is missing from the request",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body.refresh_token",
                                            "message": "Field required",
                                            "type": "missing",
                                            "meta": None,
                                        },
                                    ],
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
                                "description": "Example response when request body exceeds configured size limits",
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
                "description": "Invalid refresh token",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "invalid_refresh_token": {
                                "summary": "Invalid refresh token",
                                "description": "Example response when refresh token is invalid or expired",
                                "value": {
                                    "error": "Invalid refresh token",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "Relogin successful",
                "model": ReloginResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "relogin_success": {
                                "summary": "Relogin successful",
                                "description": "Example successful relogin response",
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
                                    "access_token": "<access_token>",
                                    "refresh_token": "<refresh_token>",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def relogin_endpoint(payload: ReloginRequest) -> ReloginResponse:  # noqa: C901
        """Relogin Endpoint.

        Arguments:
            payload (ReloginRequest): Relogin request payload.

        Returns:
            ReloginResponse: User information and tokens.

        Raises:
            HTTPException: If relogin fails.
        """

        try:
            refresh_status: str
            refresh_payload: dict[str, object] | None
            refresh_status, refresh_payload = await validate_refresh_token(token=payload.refresh_token)

            if refresh_status != "valid" or refresh_payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            raw_user_id: object = refresh_payload.get("sub")
            if not isinstance(raw_user_id, str) or not raw_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            try:
                user_uuid: uuid.UUID = uuid.UUID(raw_user_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                ) from exc

            try:
                postgresql_adapter: PostgreSQLAdapter = await get_postgresql_adapter()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            session: AsyncSession = await postgresql_adapter.get_session()

            async with session as db:
                result: Result[tuple[User]] = await db.execute(statement=select(User).where(User.id == user_uuid))
                user: User | None = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid refresh token",
                    )

                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account is not active",
                    )

            user_id_str: str = str(object=user.id)

            try:
                tokens: dict[str, str] = await get_or_create_relogin_tokens(
                    user_id=user_id_str,
                    refresh_token=payload.refresh_token,
                )
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            response = ReloginResponse(
                id=user_id_str,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
            )

            logger.info(
                msg="Relogin successful",
                extra={
                    "user_id": user_id_str,
                    "username": user.username,
                    "token_reused": tokens.get("reused") == "true",
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Relogin failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to relogin",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_relogin_routes"]
