# ruff: noqa: TC002, TC003

import logging

from fastapi import APIRouter
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
from src.schemas.auth import ReactivateAccountRequest
from src.tasks.auth.account_management import send_reactivation_initiated_email
from src.tasks.auth.account_management import send_reactivation_success_email
from src.utils.auth_tokens import cache_reactivate_token
from src.utils.auth_tokens import consume_reactivate_token
from src.utils.auth_tokens import generate_reactivate_token
from src.utils.auth_tokens import validate_reactivate_token


def register_reactivate_routes(router: APIRouter, logger: logging.Logger) -> None:  # noqa: C901, PLR0915
    """Register Reactivate Account Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.post(
        path="/reactivate",
        response_model=AccountMessageResponse,
        status_code=status.HTTP_200_OK,
        summary="Reactivate Account",
        description="Initiate account reactivation process using username or email.",
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
                            "reactivation_failed": {
                                "summary": "Reactivation failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to process reactivation request",
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
                            "both_identifiers_provided": {
                                "summary": "Multiple identifiers",
                                "description": "Example response when both username and email are provided",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body",
                                            "message": "Value error, Provide exactly one of username or email",
                                            "type": "value_error",
                                            "meta": {
                                                "error": "Provide exactly one of username or email",
                                            },
                                        },
                                    ],
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "invalid_email": {
                                "summary": "Invalid email format",
                                "description": "Example response when email is not a valid email format",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body",
                                            "message": "Value error, Invalid email format",
                                            "type": "value_error",
                                            "meta": {
                                                "error": "Invalid email format",
                                            },
                                        },
                                    ],
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "invalid_username": {
                                "summary": "Invalid username format",
                                "description": "Example response when username is not valid",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body",
                                            "message": "Value error, Username must be alphanumeric with underscores, starting with letter or number",  # noqa: E501
                                            "type": "value_error",
                                            "meta": {
                                                "error": "Username must be alphanumeric with underscores, starting with letter or number",  # noqa: E501
                                            },
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
            status.HTTP_200_OK: {
                "description": "Reactivation email sent if account exists",
                "model": AccountMessageResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "reactivation_initiated": {
                                "summary": "Reactivation initiated",
                                "description": "Example successful response when reactivation email is sent",
                                "value": {
                                    "message": "If the account exists and is inactive, a reactivation link has been sent",  # noqa: E501
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def reactivate_account_endpoint(payload: ReactivateAccountRequest) -> AccountMessageResponse:
        """Reactivate Account Endpoint.

        Arguments:
            payload (ReactivateAccountRequest): Reactivate request payload.

        Returns:
            AccountMessageResponse: Message response.

        Raises:
            HTTPException: If request fails.
        """

        try:
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
                statement: Select[tuple[User]] = select(User)
                if payload.username is not None:
                    statement: Select[tuple[User]] = statement.where(User.username == payload.username)
                else:
                    statement: Select[tuple[User]] = statement.where(User.email == payload.email)

                result: Result[tuple[User]] = await db.execute(statement=statement)
                user: User | None = result.scalar_one_or_none()

            if user is not None and not user.is_active:
                user_id_str: str = str(object=user.id)

                reactivate_token: str = await generate_reactivate_token(user_id=user_id_str)

                try:
                    await cache_reactivate_token(user_id=user_id_str, token=reactivate_token)
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=str(object=exc),
                    ) from exc

                reactivation_url: str = (
                    f"{settings.api_base_url}/api/v1/auth/reactivate-confirm?token={reactivate_token}"
                )

                try:
                    send_reactivation_initiated_email.delay(
                        to_email=user.email,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        username=user.username,
                        reactivation_url=reactivation_url,
                    )
                except Exception as email_exc:
                    logger.warning(
                        msg=f"Failed to queue reactivation email: {email_exc!s}",
                        extra={"exception_type": type(email_exc).__name__, "user_id": user_id_str},
                    )

            response = AccountMessageResponse(
                message="If the account exists and is inactive, a reactivation link has been sent",
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Reactivate account failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process reactivation request",
            ) from exc
        else:
            return response

    @router.get(
        path="/reactivate-confirm",
        response_model=AccountStatusResponse,
        status_code=status.HTTP_200_OK,
        summary="Confirm Account Reactivation",
        description="Confirm account reactivation using token from email.",
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
                            "reactivation_confirm_failed": {
                                "summary": "Reactivation confirm failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to confirm reactivation",
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
                            "missing_token": {
                                "summary": "Missing token",
                                "description": "Example response when token field is missing",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body.token",
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
                "description": "Invalid or expired reactivation token",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "invalid_token": {
                                "summary": "Invalid reactivation token",
                                "description": "Example response when reactivation token is invalid or expired",
                                "value": {
                                    "error": "Invalid or expired reactivation token",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "token_already_used": {
                                "summary": "Token already used",
                                "description": "Example response when reactivation token has already been consumed",
                                "value": {
                                    "error": "Reactivation token has already been used or is invalid",
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
                "description": "Account reactivated successfully",
                "model": AccountStatusResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "reactivation_confirmed": {
                                "summary": "Reactivation confirmed",
                                "description": "Example successful response when account is reactivated",
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
    async def reactivate_confirm_endpoint(token: str) -> AccountStatusResponse:
        """Reactivate Confirm Endpoint.

        Arguments:
            token (str): Reactivation confirmation token from email.

        Returns:
            AccountStatusResponse: Account status response.

        Raises:
            HTTPException: If request fails.
        """

        try:
            token_status: str
            token_payload: dict | None
            token_status, token_payload = await validate_reactivate_token(token=token)

            if token_status != "valid" or token_payload is None:  # noqa: S105
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired reactivation token",
                )

            user_id: str = token_payload["sub"]

            consumed: bool
            try:
                _, consumed = await consume_reactivate_token(user_id=user_id, token=token)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            if not consumed:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Reactivation token has already been used or is invalid",
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

                update_stmt = update(User).where(User.id == user_id).values(is_active=True)
                await db.execute(statement=update_stmt)
                await db.commit()
                await db.refresh(user)

            try:
                send_reactivation_success_email.delay(
                    to_email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                )
            except Exception as email_exc:
                logger.warning(
                    msg=f"Failed to queue reactivation success email: {email_exc!s}",
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
                msg="Account reactivated successfully",
                extra={"user_id": user_id, "username": user.username},
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Reactivate confirm failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm reactivation",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_reactivate_routes"]
