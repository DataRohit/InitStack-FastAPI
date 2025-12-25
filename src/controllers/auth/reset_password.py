# ruff: noqa: TC002, TC003

import logging
import uuid

from argon2 import PasswordHasher
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
from src.schemas.auth.password_reset import MessageResponse
from src.schemas.auth.password_reset import ResetPasswordRequest
from src.tasks.auth.password_reset import send_password_updated_email
from src.utils.auth_tokens import consume_reset_password_token
from src.utils.auth_tokens import revoke_login_tokens
from src.utils.auth_tokens import validate_reset_password_token


def register_reset_password_routes(  # noqa: C901, PLR0915
    router: APIRouter,
    logger: logging.Logger,
    password_hasher: PasswordHasher,
) -> None:
    """Register Reset Password Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.
        password_hasher (PasswordHasher): Password hasher.

    Returns:
        None

    Raises:
        None
    """

    @router.post(
        path="/reset-password",
        response_model=MessageResponse,
        status_code=status.HTTP_200_OK,
        summary="Reset Password",
        description="Reset a user's password using a reset token.",
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
                            "reset_password_failed": {
                                "summary": "Reset password failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to reset password",
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
                                "description": "Example response when password fields are missing",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body.password",
                                            "message": "Field required",
                                            "type": "missing",
                                            "meta": None,
                                        },
                                    ],
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "passwords_do_not_match": {
                                "summary": "Passwords do not match",
                                "description": "Example response when password and re_password do not match",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body",
                                            "message": "Value error, Passwords do not match",
                                            "type": "value_error",
                                            "meta": {
                                                "error": "Passwords do not match",
                                            },
                                        },
                                    ],
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
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
            status.HTTP_409_CONFLICT: {
                "description": "Token already used",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "token_already_used": {
                                "summary": "Token already used",
                                "description": "Example response when token is not found in Redis",
                                "value": {
                                    "error": "Reset token already used",
                                    "detail": "HTTP 409",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "User not found",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "user_not_found": {
                                "summary": "User not found",
                                "description": "Example response when the token is valid but the user does not exist",
                                "value": {
                                    "error": "User not found",
                                    "detail": "HTTP 404",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Invalid request or token",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "invalid_token": {
                                "summary": "Invalid token",
                                "description": "Example response when the reset token is invalid",
                                "value": {
                                    "error": "Invalid reset token",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "expired_token": {
                                "summary": "Expired token",
                                "description": "Example response when the reset token is expired",
                                "value": {
                                    "error": "Reset token expired",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "Password reset successfully",
                "model": MessageResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "reset_success": {
                                "summary": "Password reset",
                                "description": "Example response when password is reset successfully",
                                "value": {
                                    "message": "Password reset successfully",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def reset_password_endpoint(token: str, payload: ResetPasswordRequest) -> MessageResponse:  # noqa: C901, PLR0912, PLR0915
        """Reset Password Endpoint.

        Arguments:
            token (str): Reset password token.
            payload (ResetPasswordRequest): Reset password request payload.

        Returns:
            MessageResponse: Message response.

        Raises:
            HTTPException: If request fails.
        """

        try:
            validation_status: str
            jwt_payload: dict[str, object] | None
            validation_status, jwt_payload = await validate_reset_password_token(token=token)

            if validation_status == "expired":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token expired",
                )

            if validation_status != "valid" or jwt_payload is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token",
                )

            raw_user_id: object = jwt_payload.get("sub")
            if not isinstance(raw_user_id, str) or not raw_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token",
                )

            try:
                user_uuid: uuid.UUID = uuid.UUID(hex=raw_user_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token",
                ) from exc

            user_id_str: str = str(object=user_uuid)

            try:
                consume_status: str
                consumed: bool
                consume_status, consumed = await consume_reset_password_token(user_id=user_id_str, token=token)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            if consume_status == "already_used":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Reset token already used",
                )

            if consume_status != "consumed" or not consumed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token",
                )

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
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found",
                    )

                user.hashed_password: str = password_hasher.hash(password=payload.password)
                await db.commit()
                await db.refresh(instance=user)

            try:
                await revoke_login_tokens(user_id=user_id_str)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            try:
                send_password_updated_email.delay(
                    to_email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                )
            except Exception as email_exc:
                logger.warning(
                    msg=f"Failed to queue password updated email: {email_exc!s}",
                    extra={"exception_type": type(email_exc).__name__, "user_id": user_id_str},
                )

            response = MessageResponse(message="Password reset successfully")

            logger.info(
                msg="Password reset successfully",
                extra={"user_id": user_id_str},
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Reset password failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_reset_password_routes"]
