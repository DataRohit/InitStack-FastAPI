# ruff: noqa: TC002, TC003

import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Result
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas import ValidationErrorResponse
from src.schemas.auth.login import LoginRequest
from src.schemas.auth.login import LoginResponse
from src.utils.auth_tokens import get_or_create_login_tokens


def register_login_routes(  # noqa: C901
    router: APIRouter,
    logger: logging.Logger,
    password_hasher: PasswordHasher,
) -> None:
    """Register Login Routes On Provided Router.

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
        path="/login",
        response_model=LoginResponse,
        status_code=status.HTTP_200_OK,
        summary="Login",
        description="Authenticate a user using username/email and password.",
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
                            "login_failed": {
                                "summary": "Login failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to login",
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
                                "description": "Example response when a required field is missing from the request",
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
            status.HTTP_403_FORBIDDEN: {
                "description": "Account not active",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "account_not_active": {
                                "summary": "Account not active",
                                "description": "Example response when user credentials are correct but account is inactive",  # noqa: E501
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
                "description": "Invalid credentials",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "invalid_credentials": {
                                "summary": "Invalid credentials",
                                "description": "Example response when username/email or password is incorrect",
                                "value": {
                                    "error": "Invalid credentials",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "Login successful",
                "model": LoginResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "login_with_username": {
                                "summary": "Login with username",
                                "description": "Example successful login using username and password",
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
                            "login_with_email": {
                                "summary": "Login with email",
                                "description": "Example successful login using email and password",
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
    async def login_endpoint(payload: LoginRequest) -> LoginResponse:  # noqa: C901
        """Login Endpoint.

        Arguments:
            payload (LoginRequest): Login request payload.

        Returns:
            LoginResponse: User information and tokens.

        Raises:
            HTTPException: If login fails.
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

            async with session as db:
                statement: Select[tuple[User]] = select(User)
                if payload.username is not None:
                    statement: Select[tuple[User]] = statement.where(User.username == payload.username)
                else:
                    statement: Select[tuple[User]] = statement.where(User.email == payload.email)

                result: Result[tuple[User]] = await db.execute(statement=statement)
                user: User | None = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                    )

                if not user.hashed_password:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                    )

                try:
                    password_hasher.verify(hash=user.hashed_password, password=payload.password)
                except VerifyMismatchError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                    ) from exc

                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account is not active",
                    )

            user_id_str: str = str(object=user.id)

            try:
                tokens: dict[str, str] = await get_or_create_login_tokens(user_id=user_id_str)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            response = LoginResponse(
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
                msg="Login successful",
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
                msg=f"Login failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to login",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_login_routes"]
