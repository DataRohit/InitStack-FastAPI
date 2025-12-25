# ruff: noqa: TC002, TC003

import logging

from argon2 import PasswordHasher
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from config.settings import settings
from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas import ValidationErrorResponse
from src.schemas.auth.signup import SignUpRequest
from src.schemas.auth.signup import SignUpResponse
from src.tasks.auth.signup import send_signup_activation_email
from src.utils.auth_tokens import cache_activation_token
from src.utils.auth_tokens import generate_activation_token


def register_signup_routes(
    router: APIRouter,
    logger: logging.Logger,
    password_hasher: PasswordHasher,
) -> None:
    """Register Sign Up Routes On Provided Router.

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
        path="/signup",
        response_model=SignUpResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Sign Up",
        description="Create a new user account.",
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
                            "signup_failed": {
                                "summary": "Signup failed",
                                "description": "Example response when controller raises an internal error",
                                "value": {
                                    "error": "Failed to sign up",
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
                            "invalid_email": {
                                "summary": "Invalid email format",
                                "description": "Example response when the email field is not a valid email",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body.email",
                                            "message": "Invalid email format",
                                            "type": "value_error",
                                            "meta": {
                                                "error": "Invalid email format",
                                            },
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
                            "missing_required_field": {
                                "summary": "Missing required field",
                                "description": "Example response when a required field is missing from the request",
                                "value": {
                                    "error": "Validation Error",
                                    "errors": [
                                        {
                                            "path": "body.first_name",
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
                "description": "Username or email already exists",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "user_already_exists": {
                                "summary": "Username or email already exists",
                                "description": "Example response when username or email is already registered",
                                "value": {
                                    "error": "Username or email already exists",
                                    "detail": "HTTP 409",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_201_CREATED: {
                "description": "User created successfully",
                "model": SignUpResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "user_created": {
                                "summary": "User created",
                                "description": "Example response when a new user is created successfully",
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
                                    "updated_at": None,
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def signup_endpoint(payload: SignUpRequest) -> SignUpResponse:
        """Sign Up Endpoint.

        Arguments:
            payload (SignUpRequest): Sign up request payload.

        Returns:
            SignUpResponse: Created user information.

        Raises:
            HTTPException: If user creation fails.
        """

        try:
            logger.info(
                msg="Processing signup request",
                extra={"username": payload.username, "email": payload.email},
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
                existing_user: Result[tuple[User]] = await db.execute(
                    statement=select(User).where(
                        (User.username == payload.username) | (User.email == payload.email),
                    ),
                )
                if existing_user.scalar_one_or_none() is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Username or email already exists",
                    )

                hashed_password: str = password_hasher.hash(password=payload.password)

                user = User(
                    username=payload.username,
                    email=payload.email,
                    hashed_password=hashed_password,
                    first_name=payload.first_name,
                    last_name=payload.last_name,
                )

                db.add(instance=user)
                await db.commit()
                await db.refresh(instance=user)

            user_id_str: str = str(object=user.id)

            activation_token: str = await generate_activation_token(user_id=user_id_str)
            await cache_activation_token(user_id=user_id_str, token=activation_token)

            activation_url: str = f"{settings.api_base_url}/api/v1/auth/activate?token={activation_token}"

            try:
                send_signup_activation_email.delay(
                    to_email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                    activation_url=activation_url,
                )
            except Exception as email_exc:
                logger.warning(
                    msg=f"Failed to queue activation email: {email_exc!s}",
                    extra={
                        "exception_type": type(email_exc).__name__,
                        "user_id": user_id_str,
                    },
                )

            response = SignUpResponse(
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
            )

            logger.info(
                msg="Signup successful, activation email queued",
                extra={"user_id": user_id_str, "username": user.username},
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Signup failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sign up",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_signup_routes"]
