import datetime
from typing import TYPE_CHECKING
from typing import Any

import jwt

from config.adapters.redis import TokenCacheRedisAdapter
from config.adapters.redis import get_token_cache_redis_adapter
from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

logger: logging.Logger = get_logger(name="auth.tokens")


def _require_secret(*, secret: str, name: str) -> str:
    """Require Token Secret To Be Configured.

    Arguments:
        secret (str): Secret value.
        name (str): Setting name.

    Returns:
        str: Secret value.

    Raises:
        RuntimeError: If secret is empty.
    """

    if not secret:
        msg = f"{name} is not configured"
        raise RuntimeError(msg)
    return secret


async def generate_access_token(user_id: str) -> str:
    """Generate JWT Access Token.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT access token string.

    Raises:
        RuntimeError: If access token secret is not configured.
        Exception: If token generation fails.
    """

    secret: str = _require_secret(secret=settings.access_token_secret, name="ACCESS_TOKEN_SECRET")

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.access_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": expiry,
    }

    return jwt.encode(payload=payload, key=secret, algorithm="HS256")


async def generate_refresh_token(user_id: str) -> str:
    """Generate JWT Refresh Token.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT refresh token string.

    Raises:
        RuntimeError: If refresh token secret is not configured.
        Exception: If token generation fails.
    """

    secret: str = _require_secret(secret=settings.refresh_token_secret, name="REFRESH_TOKEN_SECRET")

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.refresh_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": expiry,
    }

    return jwt.encode(payload=payload, key=secret, algorithm="HS256")


async def validate_access_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Access Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not an access token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        RuntimeError: If access token secret is not configured.
    """

    if not token:
        return "invalid", None

    secret: str = _require_secret(secret=settings.access_token_secret, name="ACCESS_TOKEN_SECRET")

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "access":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def validate_refresh_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Refresh Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not a refresh token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        RuntimeError: If refresh token secret is not configured.
    """

    if not token:
        return "invalid", None

    secret: str = _require_secret(secret=settings.refresh_token_secret, name="REFRESH_TOKEN_SECRET")

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "refresh":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def get_or_create_login_tokens(*, user_id: str) -> dict[str, str]:
    """Get Or Create Login Tokens For User.

    Arguments:
        user_id (str): User identifier.

    Returns:
        dict[str, str]: Dictionary containing access_token and refresh_token.

    Raises:
        RuntimeError: If Redis is not enabled.
        RuntimeError: If token secrets are not configured.
        Exception: For Redis or token generation errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    access_key: str = f"access_token:{user_id}"
    refresh_key: str = f"refresh_token:{user_id}"

    cached_access: str | None = await token_cache_adapter.get(access_key)
    cached_refresh: str | None = await token_cache_adapter.get(refresh_key)

    if cached_access is not None and cached_refresh is not None:
        access_status: str
        refresh_status: str
        access_status, _ = await validate_access_token(token=cached_access)
        refresh_status, _ = await validate_refresh_token(token=cached_refresh)

        if access_status == "valid" and refresh_status == "valid":
            return {
                "access_token": cached_access,
                "refresh_token": cached_refresh,
                "reused": "true",
            }

    access_token: str = await generate_access_token(user_id=user_id)
    refresh_token: str = await generate_refresh_token(user_id=user_id)

    await token_cache_adapter.set(
        key=access_key,
        value=access_token,
        ex=settings.access_token_expiry_seconds,
    )
    await token_cache_adapter.set(
        key=refresh_key,
        value=refresh_token,
        ex=settings.refresh_token_expiry_seconds,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "reused": "false",
    }


async def get_or_create_relogin_tokens(*, user_id: str, refresh_token: str) -> dict[str, str]:
    """Get Or Create Relogin Tokens For User.

    Arguments:
        user_id (str): User identifier.
        refresh_token (str): Presented refresh token.

    Returns:
        dict[str, str]: Dictionary containing:
            - access_token (str)
            - refresh_token (str)
            - reused (str): "true" if tokens were reused else "false".

    Raises:
        RuntimeError: If Redis is not enabled.
        RuntimeError: If token secrets are not configured.
        Exception: For Redis or token generation errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    access_key: str = f"access_token:{user_id}"
    refresh_key: str = f"refresh_token:{user_id}"

    cached_access: str | None = await token_cache_adapter.get(key=access_key)
    cached_refresh: str | None = await token_cache_adapter.get(key=refresh_key)

    if cached_access is not None and cached_refresh is not None and cached_refresh == refresh_token:
        access_status: str
        refresh_status: str
        access_status, _ = await validate_access_token(token=cached_access)
        refresh_status, _ = await validate_refresh_token(token=cached_refresh)

        if access_status == "valid" and refresh_status == "valid":
            return {
                "access_token": cached_access,
                "refresh_token": cached_refresh,
                "reused": "true",
            }

    access_token: str = await generate_access_token(user_id=user_id)
    new_refresh_token: str = await generate_refresh_token(user_id=user_id)

    await token_cache_adapter.set(
        key=access_key,
        value=access_token,
        ex=settings.access_token_expiry_seconds,
    )
    await token_cache_adapter.set(
        key=refresh_key,
        value=new_refresh_token,
        ex=settings.refresh_token_expiry_seconds,
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "reused": "false",
    }


async def generate_forgot_password_token(user_id: str) -> str:
    """Generate JWT Forgot Password Token.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT forgot password token string.

    Raises:
        RuntimeError: If forgot password token secret is not configured.
        Exception: If token generation fails.
    """

    secret: str = _require_secret(secret=settings.forgot_password_token_secret, name="FORGOT_PASSWORD_TOKEN_SECRET")

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.forgot_password_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "forgot_password",
        "iat": now,
        "exp": expiry,
    }

    return jwt.encode(payload=payload, key=secret, algorithm="HS256")


async def validate_forgot_password_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Forgot Password Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not a forgot password token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        RuntimeError: If forgot password token secret is not configured.
    """

    if not token:
        return "invalid", None

    secret: str = _require_secret(secret=settings.forgot_password_token_secret, name="FORGOT_PASSWORD_TOKEN_SECRET")

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "forgot_password":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def cache_forgot_password_token(*, user_id: str, token: str) -> bool:
    """Cache Forgot Password Token In Redis With Matching Expiry.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token to cache.

    Returns:
        bool: True if cached successfully.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: If Redis operation fails.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"forgot_password_token:{user_id}"
    await token_cache_adapter.set(
        key=key,
        value=token,
        ex=settings.forgot_password_token_expiry_seconds,
    )
    return True


async def consume_forgot_password_token(*, user_id: str, token: str) -> tuple[str, bool]:
    """Consume A Forgot Password Token.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token.

    Returns:
        tuple[str, bool]: (status, consumed)

        Status values:
            - consumed: Token existed and was deleted.
            - already_used: Token does not exist in Redis.
            - mismatch: Token exists but does not match.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: For Redis errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"forgot_password_token:{user_id}"
    cached: str | None = await token_cache_adapter.get(key)
    if cached is None:
        return "already_used", False

    if cached != token:
        return "mismatch", False

    deleted_count: int = await token_cache_adapter.delete(key)
    if deleted_count <= 0:
        return "already_used", False

    return "consumed", True


async def generate_reset_password_token(user_id: str) -> str:
    """Generate JWT Reset Password Token.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT reset password token string.

    Raises:
        RuntimeError: If reset password token secret is not configured.
        Exception: If token generation fails.
    """

    secret: str = _require_secret(secret=settings.reset_password_token_secret, name="RESET_PASSWORD_TOKEN_SECRET")

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.reset_password_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "reset_password",
        "iat": now,
        "exp": expiry,
    }

    return jwt.encode(payload=payload, key=secret, algorithm="HS256")


async def validate_reset_password_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Reset Password Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not a reset password token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        RuntimeError: If reset password token secret is not configured.
    """

    if not token:
        return "invalid", None

    secret: str = _require_secret(secret=settings.reset_password_token_secret, name="RESET_PASSWORD_TOKEN_SECRET")

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "reset_password":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def cache_reset_password_token(*, user_id: str, token: str) -> bool:
    """Cache Reset Password Token In Redis With Matching Expiry.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token to cache.

    Returns:
        bool: True if cached successfully.

    Raises:
        RuntimeError: If Redis is disabled.
        Exception: If Redis operation fails.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"reset_password_token:{user_id}"

    await token_cache_adapter.set(
        key=key,
        value=token,
        ex=settings.reset_password_token_expiry_seconds,
    )

    return True


async def consume_reset_password_token(*, user_id: str, token: str) -> tuple[str, bool]:
    """Consume A Reset Password Token.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token.

    Returns:
        tuple[str, bool]: (status, consumed)

        Status values:
            - consumed: Token existed and was deleted.
            - already_used: Token does not exist in Redis.
            - mismatch: Token exists but does not match.

    Raises:
        RuntimeError: If Redis is disabled.
        Exception: For Redis errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"reset_password_token:{user_id}"
    cached: str | None = await token_cache_adapter.get(key)
    if cached is None:
        return "already_used", False

    if cached != token:
        return "mismatch", False

    deleted_count: int = await token_cache_adapter.delete(key)
    if deleted_count <= 0:
        return "already_used", False

    return "consumed", True


async def revoke_login_tokens(*, user_id: str) -> bool:
    """Revoke Cached Login Tokens For User By Deleting Redis Keys.

    This removes both:
        - access_token:{user_id}
        - refresh_token:{user_id}

    Arguments:
        user_id (str): User identifier.

    Returns:
        bool: True if operation succeeded.

    Raises:
        RuntimeError: If Redis is disabled.
        Exception: For Redis errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    access_key: str = f"access_token:{user_id}"
    refresh_key: str = f"refresh_token:{user_id}"

    await token_cache_adapter.delete(access_key)
    await token_cache_adapter.delete(refresh_key)

    return True


async def generate_activation_token(user_id: str) -> str:
    """Generate JWT Activation Token For User Signup.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT token string.

    Raises:
        Exception: If token generation fails.
    """

    logger.info(
        msg="Generating activation token",
        extra={"user_id": user_id, "expiry_seconds": settings.signup_token_expiry_seconds},
    )

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.signup_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "activation",
        "iat": now,
        "exp": expiry,
    }

    token: str = jwt.encode(payload=payload, key=settings.signup_token_secret, algorithm="HS256")

    logger.info(
        msg="Activation token generated successfully",
        extra={"user_id": user_id, "token_length": len(token)},
    )

    return token


async def cache_activation_token(user_id: str, token: str) -> bool:
    """Cache Activation Token In Redis With Matching Expiry.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token to cache.

    Returns:
        bool: True if cached successfully.

    Raises:
        Exception: If Redis operation fails.
    """

    logger.info(
        msg="Starting token caching process",
        extra={
            "user_id": user_id,
            "token_cache_db": settings.redis_token_cache_db,
            "expiry_seconds": settings.signup_token_expiry_seconds,
        },
    )

    try:
        token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()

        logger.debug(
            msg="Token cache adapter retrieved",
            extra={"is_connected": token_cache_adapter.is_connected},
        )

        if not token_cache_adapter.is_connected:
            logger.info(msg="Token cache Redis not connected, connecting now")
            await token_cache_adapter.connect()

        key: str = f"activation_token:{user_id}"

        logger.info(
            msg="Attempting to cache token in Redis",
            extra={"key": key, "expiry_seconds": settings.signup_token_expiry_seconds},
        )

        await token_cache_adapter.set(
            key=key,
            value=token,
            ex=settings.signup_token_expiry_seconds,
        )

        verify_exists: int = await token_cache_adapter.exists(key)
        logger.info(
            msg="Token cached successfully",
            extra={"key": key, "verified_exists": verify_exists > 0},
        )

        return True  # noqa: TRY300

    except Exception as exc:
        logger.exception(
            msg=f"Failed to cache activation token: {exc!s}",
            extra={"user_id": user_id, "exception_type": type(exc).__name__},
        )
        raise


async def verify_activation_token(token: str) -> dict[str, Any] | None:
    """Verify And Decode Activation Token.

    Arguments:
        token (str): JWT token to verify.

    Returns:
        dict[str, Any] | None: Decoded payload if valid, None otherwise.

    Raises:
        None
    """

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=settings.signup_token_secret,
            algorithms=["HS256"],
        )

        if payload.get("type") != "activation":
            return None

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    else:
        return payload


async def validate_activation_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Activation Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not an activation token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        None
    """

    if not token:
        return "invalid", None

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=settings.signup_token_secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "activation":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def consume_activation_token(*, user_id: str, token: str) -> tuple[str, bool]:
    """Consume Activation Token From Redis If It Matches.

    Arguments:
        user_id (str): User ID whose token is expected.
        token (str): Presented activation token.

    Returns:
        tuple[str, bool]: A tuple of (status, consumed).

        Status values:
            - consumed: Token existed in Redis, matched, and was removed.
            - already_used: Token does not exist in Redis.
            - mismatch: Token exists in Redis but does not match the presented token.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: If Redis operations fail.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()

    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"activation_token:{user_id}"
    cached: str | None = await token_cache_adapter.get(key)
    if cached is None:
        return "already_used", False

    if cached != token:
        return "mismatch", False

    deleted_count: int = await token_cache_adapter.delete(key)
    if deleted_count <= 0:
        return "already_used", False

    return "consumed", True


async def check_token_used(user_id: str) -> bool:
    """Check If Activation Token Has Been Used.

    Arguments:
        user_id (str): User ID to check.

    Returns:
        bool: True if token has been used, False if still valid.

    Raises:
        Exception: If Redis operation fails.
    """

    logger.debug(msg="Checking if token has been used", extra={"user_id": user_id})

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()

    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"activation_token:{user_id}"
    exists: int = await token_cache_adapter.exists(key)
    is_used: bool = exists == 0

    logger.info(
        msg="Token usage check completed",
        extra={"user_id": user_id, "key": key, "exists": exists, "is_used": is_used},
    )

    return is_used


async def mark_token_as_used(user_id: str) -> bool:
    """Mark Activation Token As Used By Deleting From Redis.

    Arguments:
        user_id (str): User ID.

    Returns:
        bool: True if marked successfully.

    Raises:
        Exception: If Redis operation fails.
    """

    logger.info(msg="Marking token as used", extra={"user_id": user_id})

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()

    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"activation_token:{user_id}"
    deleted_count: int = await token_cache_adapter.delete(key)
    success: bool = deleted_count > 0

    logger.info(
        msg="Token marked as used",
        extra={"user_id": user_id, "key": key, "deleted_count": deleted_count, "success": success},
    )

    return success


async def generate_deactivate_token(user_id: str) -> str:
    """Generate JWT Deactivate Token.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT deactivate token string.

    Raises:
        RuntimeError: If deactivate token secret is not configured.
        Exception: If token generation fails.
    """

    secret: str = _require_secret(secret=settings.deactivate_token_secret, name="DEACTIVATE_TOKEN_SECRET")

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.deactivate_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "deactivate",
        "iat": now,
        "exp": expiry,
    }

    return jwt.encode(payload=payload, key=secret, algorithm="HS256")


async def validate_deactivate_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Deactivate Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not a deactivate token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        RuntimeError: If deactivate token secret is not configured.
    """

    if not token:
        return "invalid", None

    secret: str = _require_secret(secret=settings.deactivate_token_secret, name="DEACTIVATE_TOKEN_SECRET")

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "deactivate":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def cache_deactivate_token(*, user_id: str, token: str) -> bool:
    """Cache Deactivate Token In Redis With Matching Expiry.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token to cache.

    Returns:
        bool: True if cached successfully.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: If Redis operation fails.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"deactivate_token:{user_id}"
    await token_cache_adapter.set(
        key=key,
        value=token,
        ex=settings.deactivate_token_expiry_seconds,
    )

    return True


async def consume_deactivate_token(*, user_id: str, token: str) -> tuple[str, bool]:
    """Consume A Deactivate Token.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token.

    Returns:
        tuple[str, bool]: (status, consumed)

        Status values:
            - consumed: Token existed and was deleted.
            - already_used: Token does not exist in Redis.
            - mismatch: Token exists but does not match.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: For Redis errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"deactivate_token:{user_id}"
    cached: str | None = await token_cache_adapter.get(key)
    if cached is None:
        return "already_used", False

    if cached != token:
        return "mismatch", False

    deleted_count: int = await token_cache_adapter.delete(key)
    if deleted_count <= 0:
        return "already_used", False

    return "consumed", True


async def generate_reactivate_token(user_id: str) -> str:
    """Generate JWT Reactivate Token.

    Arguments:
        user_id (str): User ID to encode in token.

    Returns:
        str: JWT reactivate token string.

    Raises:
        RuntimeError: If reactivate token secret is not configured.
        Exception: If token generation fails.
    """

    secret: str = _require_secret(secret=settings.reactivate_token_secret, name="REACTIVATE_TOKEN_SECRET")

    now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
    expiry: datetime.datetime = now + datetime.timedelta(seconds=settings.reactivate_token_expiry_seconds)

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "reactivate",
        "iat": now,
        "exp": expiry,
    }

    return jwt.encode(payload=payload, key=secret, algorithm="HS256")


async def validate_reactivate_token(token: str) -> tuple[str, dict[str, Any] | None]:
    """Validate Reactivate Token And Return A Status.

    Arguments:
        token (str): JWT token to validate.

    Returns:
        tuple[str, dict[str, Any] | None]: A tuple of (status, payload).

        Status values:
            - valid: Token is valid and payload is returned.
            - expired: Token signature is expired.
            - invalid: Token cannot be decoded or signature is invalid.
            - wrong_type: Token decodes but is not a reactivate token.
            - missing_subject: Token decodes but is missing the subject (sub).

    Raises:
        RuntimeError: If reactivate token secret is not configured.
    """

    if not token:
        return "invalid", None

    secret: str = _require_secret(secret=settings.reactivate_token_secret, name="REACTIVATE_TOKEN_SECRET")

    try:
        payload: dict[str, Any] = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return "expired", None
    except jwt.InvalidTokenError:
        return "invalid", None

    if payload.get("type") != "reactivate":
        return "wrong_type", None

    subject: Any = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        return "missing_subject", None

    return "valid", payload


async def cache_reactivate_token(*, user_id: str, token: str) -> bool:
    """Cache Reactivate Token In Redis With Matching Expiry.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token to cache.

    Returns:
        bool: True if cached successfully.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: If Redis operation fails.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"reactivate_token:{user_id}"
    await token_cache_adapter.set(
        key=key,
        value=token,
        ex=settings.reactivate_token_expiry_seconds,
    )

    return True


async def consume_reactivate_token(*, user_id: str, token: str) -> tuple[str, bool]:
    """Consume A Reactivate Token.

    Arguments:
        user_id (str): User ID.
        token (str): JWT token.

    Returns:
        tuple[str, bool]: (status, consumed)

        Status values:
            - consumed: Token existed and was deleted.
            - already_used: Token does not exist in Redis.
            - mismatch: Token exists but does not match.

    Raises:
        RuntimeError: If Redis is not enabled.
        Exception: For Redis errors.
    """

    token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
    if not token_cache_adapter.is_connected:
        await token_cache_adapter.connect()

    key: str = f"reactivate_token:{user_id}"
    cached: str | None = await token_cache_adapter.get(key)
    if cached is None:
        return "already_used", False

    if cached != token:
        return "mismatch", False

    deleted_count: int = await token_cache_adapter.delete(key)
    if deleted_count <= 0:
        return "already_used", False

    return "consumed", True


__all__: list[str] = [
    "cache_activation_token",
    "cache_deactivate_token",
    "cache_forgot_password_token",
    "cache_reactivate_token",
    "cache_reset_password_token",
    "check_token_used",
    "consume_activation_token",
    "consume_deactivate_token",
    "consume_forgot_password_token",
    "consume_reactivate_token",
    "consume_reset_password_token",
    "generate_access_token",
    "generate_activation_token",
    "generate_deactivate_token",
    "generate_forgot_password_token",
    "generate_reactivate_token",
    "generate_refresh_token",
    "generate_reset_password_token",
    "get_or_create_login_tokens",
    "get_or_create_relogin_tokens",
    "mark_token_as_used",
    "revoke_login_tokens",
    "validate_access_token",
    "validate_activation_token",
    "validate_deactivate_token",
    "validate_forgot_password_token",
    "validate_reactivate_token",
    "validate_refresh_token",
    "validate_reset_password_token",
    "verify_activation_token",
]
