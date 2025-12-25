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
from src.schemas.auth.activate import ActivateAccountResponse
from src.tasks.auth.activate import send_activation_success_email
from src.utils.auth_tokens import consume_activation_token
from src.utils.auth_tokens import validate_activation_token


def register_activation_routes(router: APIRouter, logger: logging.Logger) -> None:  # noqa: C901, PLR0915
    """Register Activation Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.

    Returns:
        None

    Raises:
        None
    """

    @router.get(
        path="/activate",
        response_model=ActivateAccountResponse,
        status_code=status.HTTP_200_OK,
        summary="Activate Account",
        description="Activate a user account using a signup activation token.",
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
                            "activation_failed": {
                                "summary": "Activation failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to activate account",
                                    "detail": "HTTP 500",
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
                                    "error": "Too Many Requests",
                                    "detail": "Rate limit exceeded. Try again in 30 seconds.",
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
            status.HTTP_409_CONFLICT: {
                "description": "Token already used or account already active",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "token_already_used": {
                                "summary": "Token already used",
                                "description": "Example response when token is valid but not found in Redis",
                                "value": {
                                    "error": "Activation token already used",
                                    "detail": "HTTP 409",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "account_already_active": {
                                "summary": "Account already active",
                                "description": "Example response when user account is already active",
                                "value": {
                                    "error": "Account already activated",
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
                                "description": "Example response when the activation token is invalid",
                                "value": {
                                    "error": "Invalid activation token",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "expired_token": {
                                "summary": "Expired token",
                                "description": "Example response when the activation token is expired",
                                "value": {
                                    "error": "Activation token expired",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "wrong_token_type": {
                                "summary": "Wrong token type",
                                "description": "Example response when token is not an activation token",
                                "value": {
                                    "error": "Invalid activation token",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "token_mismatch": {
                                "summary": "Token mismatch",
                                "description": "Example response when token exists in Redis but does not match",
                                "value": {
                                    "error": "Invalid activation token",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                            "invalid_user_id": {
                                "summary": "Invalid user id in token",
                                "description": "Example response when token subject is not a valid UUID",
                                "value": {
                                    "error": "Invalid activation token",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "Account activated successfully",
                "model": ActivateAccountResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "activated": {
                                "summary": "Account activated",
                                "description": "Example response when account is activated successfully",
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
    async def activate_endpoint(token: str) -> ActivateAccountResponse:  # noqa: C901, PLR0912, PLR0915
        """Activate Account Endpoint.

        Arguments:
            token (str): Activation token.

        Returns:
            ActivateAccountResponse: Activated user information.

        Raises:
            HTTPException: If activation fails.
        """

        try:
            validation_status: str
            payload: dict[str, object] | None
            validation_status, payload = await validate_activation_token(token=token)

            if validation_status == "expired":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Activation token expired",
                )

            if validation_status != "valid" or payload is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid activation token",
                )

            raw_user_id: object = payload.get("sub")
            if not isinstance(raw_user_id, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid activation token",
                )

            try:
                user_uuid: uuid.UUID = uuid.UUID(raw_user_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid activation token",
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
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found",
                    )

                if user.is_active:
                    try:
                        await consume_activation_token(user_id=str(object=user_uuid), token=token)
                    except Exception as cleanup_exc:
                        logger.warning(
                            msg=f"Failed to cleanup activation token: {cleanup_exc!s}",
                            extra={"exception_type": type(cleanup_exc).__name__, "user_id": str(object=user_uuid)},
                        )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Account already activated",
                    )

                try:
                    consume_status: str
                    consumed: bool
                    consume_status, consumed = await consume_activation_token(
                        user_id=str(object=user_uuid),
                        token=token,
                    )
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=str(object=exc),
                    ) from exc

                if consume_status == "already_used":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Activation token already used",
                    )

                if consume_status != "consumed" or not consumed:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid activation token",
                    )

                user.is_active = True
                await db.commit()
                await db.refresh(instance=user)

            try:
                send_activation_success_email.delay(
                    to_email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                )
            except Exception as email_exc:
                logger.warning(
                    msg=f"Failed to queue activation success email: {email_exc!s}",
                    extra={
                        "exception_type": type(email_exc).__name__,
                        "user_id": str(object=user_uuid),
                    },
                )

            response = ActivateAccountResponse(
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

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Activation failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate account",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_activation_routes"]
