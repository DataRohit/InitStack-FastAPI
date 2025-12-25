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
    "generate_activation_token",
    "mark_token_as_used",
    "verify_activation_token",
]
