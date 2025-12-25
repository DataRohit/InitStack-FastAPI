# ruff: noqa: TC002, TC003

import logging

from argon2 import PasswordHasher
from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import Result
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from config.settings import settings
from src.models.users import OAuthAccount
from src.models.users import User
from src.schemas import ErrorResponse
from src.schemas.auth.oauth import OAuthLoginResponse
from src.tasks.auth.oauth import send_oauth_signup_email
from src.utils.auth_tokens import get_or_create_login_tokens
from src.utils.oauth_client import oauth


def register_google_oauth_routes(  # noqa: C901, PLR0915
    router: APIRouter,
    logger: logging.Logger,
    password_hasher: PasswordHasher,
) -> None:
    """Register Google OAuth Routes On Provided Router.

    Arguments:
        router (APIRouter): Router to register routes on.
        logger (logging.Logger): Logger instance.
        password_hasher (PasswordHasher): Password hasher.

    Returns:
        None

    Raises:
        None
    """

    @router.get(
        path="/google/login",
        status_code=status.HTTP_200_OK,
        summary="Google OAuth Login",
        description="Get Google OAuth authorization URL for user to complete authentication.",
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": "OAuth service not configured",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "oauth_not_configured": {
                                "summary": "OAuth not configured",
                                "description": "Example response when Google OAuth credentials are not configured",
                                "value": {
                                    "error": "Google OAuth is not configured",
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
                            "oauth_failed": {
                                "summary": "OAuth URL generation failed",
                                "description": "Example response when OAuth URL generation fails",
                                "value": {
                                    "error": "Failed to generate Google OAuth URL",
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
            status.HTTP_200_OK: {
                "description": "Authorization URL generated successfully",
                "content": {
                    "application/json": {
                        "examples": {
                            "success": {
                                "summary": "Authorization URL",
                                "description": "Example successful response with Google authorization URL",
                                "value": {
                                    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=...",
                                    "provider": "google",
                                },
                            },
                        },
                    },
                },
            },
        },
    )
    async def google_login_endpoint(request: Request) -> dict[str, str]:
        """Google OAuth Login Endpoint.

        Arguments:
            request (Request): FastAPI request object.

        Returns:
            dict[str, str]: Authorization URL and provider name.

        Raises:
            HTTPException: If OAuth URL generation fails.
        """

        try:
            if not settings.oauth_google_client_id or not settings.oauth_google_client_secret:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Google OAuth is not configured",
                )

            redirect_base: str = settings.oauth_redirect_base_url or settings.api_base_url
            redirect_uri: str = f"{redirect_base}/api/v1/auth/google/callback"

            authorization_url: str = await oauth.google.authorize_redirect(request, redirect_uri)

            return {
                "authorization_url": str(authorization_url.headers.get("location")),
                "provider": "google",
            }

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Google OAuth URL generation failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate Google OAuth URL",
            ) from exc

    @router.get(
        path="/google/callback",
        response_model=OAuthLoginResponse,
        status_code=status.HTTP_200_OK,
        summary="Google OAuth Callback",
        description="Handle Google OAuth callback and authenticate user.",
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
                            "oauth_callback_failed": {
                                "summary": "OAuth callback failed",
                                "description": "Example response when OAuth callback processing fails",
                                "value": {
                                    "error": "Failed to process Google OAuth callback",
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
                "description": "OAuth authorization failed",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "oauth_error": {
                                "summary": "OAuth authorization failed",
                                "description": "Example response when OAuth authorization fails",
                                "value": {
                                    "error": "Google OAuth authorization failed",
                                    "detail": "HTTP 401",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "OAuth error from provider",
                "model": ErrorResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "provider_error": {
                                "summary": "Provider error",
                                "description": "Example response when Google returns an error",
                                "value": {
                                    "error": "OAuth provider error: access_denied",
                                    "detail": "HTTP 400",
                                    "timestamp": "2025-01-01T12:34:56Z",
                                },
                            },
                        },
                    },
                },
            },
            status.HTTP_200_OK: {
                "description": "OAuth login successful",
                "model": OAuthLoginResponse,
                "content": {
                    "application/json": {
                        "examples": {
                            "new_user": {
                                "summary": "New user created",
                                "description": "Example successful OAuth login with new user creation",
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
                            "existing_user": {
                                "summary": "Existing user login",
                                "description": "Example successful OAuth login with existing user",
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
    async def google_callback_endpoint(request: Request) -> OAuthLoginResponse:  # noqa: C901, PLR0912, PLR0915
        """Google OAuth Callback Endpoint.

        Arguments:
            request (Request): FastAPI request object.

        Returns:
            OAuthLoginResponse: User information and tokens.

        Raises:
            HTTPException: If OAuth callback processing fails.
        """

        try:
            try:
                token: dict = await oauth.google.authorize_access_token(request)
            except OAuthError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OAuth provider error: {exc.error}",
                ) from exc

            userinfo: dict = token.get("userinfo")
            if not userinfo:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google OAuth authorization failed",
                )

            email: str | None = userinfo.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google OAuth authorization failed",
                )

            given_name: str = userinfo.get("given_name", "User")
            family_name: str = userinfo.get("family_name", "Name")
            google_id: str = userinfo.get("sub")

            try:
                postgresql_adapter: PostgreSQLAdapter = await get_postgresql_adapter()
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            session: AsyncSession = await postgresql_adapter.get_session()

            async with session as db:
                statement: Select[tuple[User]] = select(User).where(User.email == email)
                result: Result[tuple[User]] = await db.execute(statement=statement)
                user: User | None = result.scalar_one_or_none()

                is_new_user: bool = False

                if user is None:
                    is_new_user: bool = True

                    username_base: str = email.split("@")[0].lower().replace(".", "_").replace("-", "_")
                    username: str = username_base

                    counter: int = 1
                    while True:
                        existing: Result[tuple[User]] = await db.execute(
                            statement=select(User).where(User.username == username),
                        )
                        if existing.scalar_one_or_none() is None:
                            break
                        username: str = f"{username_base}_{counter}"
                        counter += 1

                    user = User(
                        username=username,
                        email=email,
                        hashed_password=None,
                        first_name=given_name,
                        last_name=family_name,
                        is_active=True,
                    )

                    db.add(instance=user)
                    await db.commit()
                    await db.refresh(instance=user)

                oauth_statement: Select[tuple[OAuthAccount]] = select(OAuthAccount).where(
                    OAuthAccount.user_id == user.id,
                    OAuthAccount.provider == "google",
                )
                oauth_result: Result[tuple[OAuthAccount]] = await db.execute(statement=oauth_statement)
                oauth_account: OAuthAccount | None = oauth_result.scalar_one_or_none()

                if oauth_account is None:
                    oauth_account = OAuthAccount(
                        user_id=user.id,
                        provider="google",
                        provider_account_id=google_id,
                        email=email,
                    )
                    db.add(instance=oauth_account)
                    await db.commit()

            user_id_str: str = str(object=user.id)

            try:
                tokens: dict[str, str] = await get_or_create_login_tokens(user_id=user_id_str)
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=str(object=exc),
                ) from exc

            if is_new_user:
                try:
                    send_oauth_signup_email.delay(
                        to_email=user.email,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        username=user.username,
                        provider="Google",
                    )
                except Exception as email_exc:
                    logger.warning(
                        msg=f"Failed to queue OAuth signup email: {email_exc!s}",
                        extra={
                            "exception_type": type(email_exc).__name__,
                            "user_id": user_id_str,
                        },
                    )

            response = OAuthLoginResponse(
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
                msg="Google OAuth login successful",
                extra={
                    "user_id": user_id_str,
                    "username": user.username,
                    "is_new_user": is_new_user,
                    "token_reused": tokens.get("reused") == "true",
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                msg=f"Google OAuth callback failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process Google OAuth callback",
            ) from exc
        else:
            return response


__all__: list[str] = ["register_google_oauth_routes"]
