# ruff: noqa: TC002, TC003

import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Result
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from config.settings import settings
from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas import ValidationErrorResponse
from src.schemas.auth import AccountMessageResponse
from src.schemas.auth import AccountStatusResponse
from src.tasks.auth.account_management import send_deactivation_initiated_email
from src.tasks.auth.account_management import send_deactivation_success_email
from src.utils.auth_tokens import cache_deactivate_token
from src.utils.auth_tokens import consume_deactivate_token
from src.utils.auth_tokens import generate_deactivate_token
from src.utils.auth_tokens import revoke_login_tokens
from src.utils.auth_tokens import validate_deactivate_token
from src.utils.jwt_auth import get_current_user


def register_deactivate_routes(router: APIRouter, logger: logging.Logger) -> None:  # noqa: C901, PLR0915
    """Register Deactivate Account Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.post(
        path="/deactivate",
        response_model=AccountMessageResponse,
        status_code=status.HTTP_200_OK,
        summary="Deactivate Account",
        description="Initiate account deactivation process.",
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
                            "deactivation_failed": {
                                "summary": "Deactivation failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to process deactivation request",
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
                            "validation_error": {
                                "summary": "Validation error",
                                "description": "Example response when request validation fails",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body.field",
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
                "description": "Account is already inactive",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "account_already_inactive": {
                                "summary": "Account already inactive",
                                "description": "Example response when user account is already deactivated",
                                "value": {
                                    "error": "Account is already inactive",
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
                "description": "Deactivation email sent",
                "model": AccountMessageResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "deactivation_initiated": {
                                "summary": "Deactivation initiated",
                                "description": "Example successful response when deactivation email is sent",
                                "value": {
                                    "message": "Deactivation confirmation email sent",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def deactivate_account_endpoint(
        current_user: Annotated[User, Depends(dependency=get_current_user)],
    ) -> AccountMessageResponse:
        """Deactivate Account Endpoint.

        Arguments:
            current_user (User): Authenticated user from Authorization header.

        Returns:
            AccountMessageResponse: Message response.

        Raises:
            HTTPException: If request fails.
        """

        try:
            user_id: str = str(object=current_user.id)

            if not current_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is already inactive",
                )

            deactivate_token: str = await generate_deactivate_token(user_id=user_id)

            try:
                await cache_deactivate_token(user_id=user_id, token=deactivate_token)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            deactivation_url: str = f"{settings.api_base_url}/api/v1/auth/deactivate-confirm?token={deactivate_token}"

            try:
                send_deactivation_initiated_email.delay(
                    to_email=current_user.email,
                    first_name=current_user.first_name,
                    last_name=current_user.last_name,
                    username=current_user.username,
                    deactivation_url=deactivation_url,
                )
            except Exception as email_exc:
                logger.warning(
                    msg=f"Failed to queue deactivation email: {email_exc!s}",
                    extra={"exception_type": type(email_exc).__name__, "user_id": user_id},
                )

            response = AccountMessageResponse(message="Deactivation confirmation email sent")

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Deactivate account failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process deactivation request",
            ) from exc
        else:
            return response

    @router.get(
        path="/deactivate-confirm",
        response_model=AccountStatusResponse,
        status_code=status.HTTP_200_OK,
        summary="Confirm Account Deactivation",
        description="Confirm account deactivation using token from email.",
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
                            "deactivation_confirm_failed": {
                                "summary": "Deactivation confirm failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to confirm deactivation",
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
                            "missing_required_query_param": {
                                "summary": "Missing required query parameter",
                                "description": "Example response when token query parameter is missing",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "query.token",
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
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Invalid or expired deactivation token",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "invalid_token": {
                                "summary": "Invalid deactivation token",
                                "description": "Example response when deactivation token is invalid or expired",
                                "value": {
                                    "error": "Invalid or expired deactivation token",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "token_already_used": {
                                "summary": "Token already used",
                                "description": "Example response when deactivation token has already been consumed",
                                "value": {
                                    "error": "Deactivation token has already been used or is invalid",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "user_not_found": {
                                "summary": "User not found",
                                "description": "Example response when user associated with token does not exist",
                                "value": {
                                    "error": "User not found",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "Account deactivated successfully",
                "model": AccountStatusResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "deactivation_confirmed": {
                                "summary": "Deactivation confirmed",
                                "description": "Example successful response when account is deactivated",
                                "value": {
                                    "id": "b2c1f7c6-1e27-4f2e-9b92-27d0f0f7c9a1",
                                    "username": "john_doe",
                                    "email": "user@example.com",
                                    "first_name": "John",
                                    "last_name": "Doe",
                                    "is_active": False,
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
    async def deactivate_confirm_endpoint(token: str) -> AccountStatusResponse:  # noqa: C901
        """Deactivate Confirm Endpoint.

        Arguments:
            token (str): Deactivation confirmation token from email.

        Returns:
            AccountStatusResponse: Account status response.

        Raises:
            HTTPException: If request fails.
        """

        try:
            token_status: str
            token_payload: dict | None
            token_status, token_payload = await validate_deactivate_token(token=token)

            if token_status != "valid" or token_payload is None:  # noqa: S105
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired deactivation token",
                )

            user_id: str = token_payload["sub"]

            consumed: bool
            try:
                _, consumed = await consume_deactivate_token(user_id=user_id, token=token)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            if not consumed:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Deactivation token has already been used or is invalid",
                )

            try:
                postgresql_adapter: PostgreSQLAdapter = await get_postgresql_adapter()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            session: AsyncSession = await postgresql_adapter.get_session()

            user: User | None = None
            async with session as db:
                statement: Select[tuple[User]] = select(User).where(User.id == user_id)
                result: Result[tuple[User]] = await db.execute(statement=statement)
                user: User | None = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                    )

                update_stmt = update(User).where(User.id == user_id).values(is_active=False)
                await db.execute(statement=update_stmt)
                await db.commit()
                await db.refresh(user)

            try:
                await revoke_login_tokens(user_id=user_id)
            except RuntimeError as exc:
                logger.warning(
                    msg=f"Failed to revoke login tokens: {exc!s}",
                    extra={"exception_type": type(exc).__name__, "user_id": user_id},
                )

            try:
                send_deactivation_success_email.delay(
                    to_email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                )
            except Exception as email_exc:
                logger.warning(
                    msg=f"Failed to queue deactivation success email: {email_exc!s}",
                    extra={"exception_type": type(email_exc).__name__, "user_id": user_id},
                )

            response = AccountStatusResponse(
                id=str(object=user.id),
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

            logger.info(
                msg="Account deactivated successfully",
                extra={"user_id": user_id, "username": user.username},
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Deactivate confirm failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm deactivation",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_deactivate_routes"]
