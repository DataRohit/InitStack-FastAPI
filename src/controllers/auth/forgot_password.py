# ruff: noqa: TC002, TC003

import logging

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Result
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from config.settings import settings
from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas import ValidationErrorResponse
from src.schemas.auth.password_reset import ForgotPasswordRequest
from src.schemas.auth.password_reset import MessageResponse
from src.tasks.auth.password_reset import send_password_reset_email
from src.utils.auth_tokens import cache_reset_password_token
from src.utils.auth_tokens import generate_reset_password_token
from src.utils.auth_tokens import revoke_login_tokens


def register_forgot_password_routes(router: APIRouter, logger: logging.Logger) -> None:  # noqa: C901
    """Register Forgot Password Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.post(
        path="/forgot-password",
        response_model=MessageResponse,
        status_code=status.HTTP_200_OK,
        summary="Forgot Password",
        description="Send a password reset link to the user using username or email.",
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
                            "forgot_password_failed": {
                                "summary": "Forgot password failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to process forgot password",
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
                "description": "Password reset email initiated",
                "model": MessageResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "initiated": {
                                "summary": "Initiated",
                                "description": "Example response when request is accepted",
                                "value": {
                                    "message": "If the account exists, a reset link has been sent",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def forgot_password_endpoint(payload: ForgotPasswordRequest) -> MessageResponse:
        """Forgot Password Endpoint.

        Arguments:
            payload (ForgotPasswordRequest): Forgot password request payload.

        Returns:
            MessageResponse: Message response.

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

            if user is not None:
                user_id_str: str = str(object=user.id)

                try:
                    await revoke_login_tokens(user_id=user_id_str)
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=str(object=exc),
                    ) from exc

                reset_token: str = await generate_reset_password_token(user_id=user_id_str)

                try:
                    await cache_reset_password_token(user_id=user_id_str, token=reset_token)
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=str(object=exc),
                    ) from exc

                reset_url: str = f"{settings.api_base_url}/api/v1/auth/reset-password?token={reset_token}"

                try:
                    send_password_reset_email.delay(
                        to_email=user.email,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        username=user.username,
                        reset_url=reset_url,
                    )
                except Exception as email_exc:
                    logger.warning(
                        msg=f"Failed to queue password reset email: {email_exc!s}",
                        extra={"exception_type": type(email_exc).__name__, "user_id": user_id_str},
                    )

            response = MessageResponse(message="If the account exists, a reset link has been sent")

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Forgot password failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process forgot password",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_forgot_password_routes"]
