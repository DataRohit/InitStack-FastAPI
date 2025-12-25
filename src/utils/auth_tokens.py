import datetime
from typing import TYPE_CHECKING
from typing import Any

import jwt

from config.adapters.redis import get_token_cache_redis_adapter
from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from config.adapters.redis import TokenCacheRedisAdapter

logger: logging.Logger = get_logger(name="auth.tokens")


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

    Token exists in Redis = not used yet.
    Token does not exist in Redis = already used.

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


__all__: list[str] = [
    "cache_activation_token",
    "check_token_used",
    "consume_activation_token",
    "generate_activation_token",
    "mark_token_as_used",
    "validate_activation_token",
    "verify_activation_token",
]
