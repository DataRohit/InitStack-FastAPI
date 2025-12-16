from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

from redis.asyncio import ConnectionPool
from redis.asyncio import Redis

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from redis.typing import ResponseT


class RedisAdapter:
    """Professional Production-Grade Redis Database Adapter.

    Inherits:
        object

    Attributes:
        _client (Redis): Async Redis client instance.
        _pool (ConnectionPool): Redis connection pool.
        _logger (logging.Logger): Logger instance for Redis operations.
        _is_connected (bool): Connection status flag.

    Properties:
        client: Get Redis client instance.
        is_connected: Get connection status.
        pool_stats: Get connection pool statistics.

    Methods:
        connect: Establish Redis connection.
        disconnect: Close Redis connection.
        health_check: Perform Redis health check.
        get: Get value by key.
        set: Set key-value pair.
        delete: Delete key.
        exists: Check if key exists.
        expire: Set key expiration.
        ttl: Get key time-to-live.
        incr: Increment key value.
        decr: Decrement key value.
        hget: Get hash field value.
        hset: Set hash field value.
        hgetall: Get all hash fields.
        hdel: Delete hash field.
        hexists: Check if hash field exists.
        lpush: Push to list left.
        rpush: Push to list right.
        lpop: Pop from list left.
        rpop: Pop from list right.
        llen: Get list length.
        lrange: Get list range.
        sadd: Add to set.
        srem: Remove from set.
        smembers: Get set members.
        sismember: Check set membership.
        zadd: Add to sorted set.
        zrem: Remove from sorted set.
        zrange: Get sorted set range.
        zscore: Get sorted set score.
        publish: Publish message to channel.
        execute_pipeline: Execute Redis pipeline.
        execute_transaction: Execute Redis transaction.
        scan_keys: Scan keys with pattern.
        flush_database: Flush current database.
        get_info: Get Redis server info.
        _create_connection_pool: Create Redis connection pool.
        _build_redis_url: Build Redis connection URL.
    """

    def __init__(self) -> None:
        """Initialize Redis Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="redis.adapter")
        self._client: Redis | None = None
        self._pool: ConnectionPool | None = None
        self._is_connected: bool = False

        self._logger.info(
            msg="Redis adapter initialized",
            extra={
                "redis_host": settings.redis_host,
                "redis_port": settings.redis_port,
                "redis_database": settings.redis_database,
                "redis_ssl": settings.redis_ssl,
                "max_connections": settings.redis_max_connections,
            },
        )

    @property
    def client(self) -> Redis:
        """Get Redis Client Instance.

        Arguments:
            None

        Returns:
            Redis: Redis client instance.

        Raises:
            RuntimeError: If Redis client is not connected.
        """

        if not self._client or not self._is_connected:
            msg = "Redis client is not connected. Call connect() first."
            raise RuntimeError(msg)

        return self._client

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to Redis, False otherwise.

        Raises:
            None
        """

        return self._is_connected

    @property
    def pool_stats(self) -> dict[str, Any]:
        """Get Connection Pool Statistics.

        Arguments:
            None

        Returns:
            dict[str, Any]: Connection pool statistics.

        Raises:
            None
        """

        if not self._pool:
            return {"status": "not_initialized"}

        try:
            stats: dict[str, Any] = {
                "max_connections": getattr(self._pool, "max_connections", "unknown"),
                "status": "initialized",
            }

            if hasattr(self._pool, "_available_connections"):
                stats["available_connections"] = len(self._pool._available_connections)  # noqa: SLF001

            if hasattr(self._pool, "_in_use_connections"):
                stats["in_use_connections"] = len(self._pool._in_use_connections)  # noqa: SLF001

            if hasattr(self._pool, "_created_connections"):
                stats["created_connections"] = self._pool._created_connections  # noqa: SLF001

        except Exception:
            return {"status": "error_getting_stats"}

        else:
            return stats

    async def connect(self) -> bool:
        """Establish Redis Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="Redis client is already connected")
                return True

            self._logger.info(msg="Establishing Redis connection")

            self._pool: ConnectionPool = self._create_connection_pool()
            self._client = Redis(connection_pool=self._pool)

            await self._client.ping()  # ty:ignore[invalid-await]
            self._is_connected = True

            self._logger.info(
                msg="Redis connection established successfully",
                extra={
                    "redis_host": settings.redis_host,
                    "redis_port": settings.redis_port,
                    "redis_database": settings.redis_database,
                    "pool_stats": self.pool_stats,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish Redis connection: {exc!s}",
                extra={
                    "redis_host": settings.redis_host,
                    "redis_port": settings.redis_port,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close Redis Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="Redis client is not connected")
                return

            self._logger.info(msg="Closing Redis connection")

            if self._client:
                await self._client.aclose()
                self._client = None

            if self._pool:
                await self._pool.aclose()
                self._pool = None

            self._is_connected = False

            self._logger.info(msg="Redis connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing Redis connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform Redis Health Check.

        Arguments:
            None

        Returns:
            bool: True if Redis is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing Redis health check")

            await self._client.ping()  # ty:ignore[possibly-missing-attribute, invalid-await]
            info = await self._client.info()  # ty:ignore[possibly-missing-attribute]

            is_healthy: bool = info.get("redis_version") is not None

            self._logger.debug(
                msg=f"Redis health check completed: {'healthy' if is_healthy else 'unhealthy'}",
                extra={
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "is_healthy": is_healthy,
                },
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"Redis health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return is_healthy

    async def get(self, key: str) -> str | None:
        """Get Value By Key.

        Arguments:
            key (str): Redis key.

        Returns:
            str | None: Value if key exists, None otherwise.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(msg="Getting value from Redis", extra={"key": key})

            value = await self.client.get(name=key)

            self._logger.debug(
                msg="Value retrieved from Redis",
                extra={"key": key, "value_exists": value is not None},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get value from Redis: {exc!s}",
                extra={"key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return value

    async def set(  # noqa: PLR0913
        self,
        key: str,
        value: str | float | bytes,
        *,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set Key-Value Pair.

        Arguments:
            key (str): Redis key.
            value (str | float | bytes): Value to set.
            ex (int | None): Expiration time in seconds.
            px (int | None): Expiration time in milliseconds.
            nx (bool): Set only if key does not exist.
            xx (bool): Set only if key exists.

        Returns:
            bool: True if operation successful, False otherwise.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Setting value in Redis",
                extra={"key": key, "ex": ex, "px": px, "nx": nx, "xx": xx},
            )

            result: ResponseT = await self.client.set(name=key, value=value, ex=ex, px=px, nx=nx, xx=xx)

            self._logger.debug(
                msg="Value set in Redis",
                extra={"key": key, "success": bool(result)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to set value in Redis: {exc!s}",
                extra={"key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return bool(result)

    async def delete(self, *keys: str) -> int:
        """Delete Key(s).

        Arguments:
            *keys (str): Redis keys to delete.

        Returns:
            int: Number of keys deleted.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(msg="Deleting keys from Redis", extra={"keys": keys})

            count: ResponseT = await self.client.delete(*keys)

            self._logger.debug(
                msg="Keys deleted from Redis",
                extra={"keys": keys, "deleted_count": count},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete keys from Redis: {exc!s}",
                extra={"keys": keys, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return count

    async def exists(self, *keys: str) -> int:
        """Check If Key(s) Exist.

        Arguments:
            *keys (str): Redis keys to check.

        Returns:
            int: Number of existing keys.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(msg="Checking key existence in Redis", extra={"keys": keys})

            count: ResponseT = await self.client.exists(*keys)

            self._logger.debug(
                msg="Key existence checked in Redis",
                extra={"keys": keys, "existing_count": count},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to check key existence in Redis: {exc!s}",
                extra={"keys": keys, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return count

    async def expire(self, key: str, time: int) -> bool:
        """Set Key Expiration.

        Arguments:
            key (str): Redis key.
            time (int): Expiration time in seconds.

        Returns:
            bool: True if expiration set, False if key does not exist.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Setting key expiration in Redis",
                extra={"key": key, "expiration_seconds": time},
            )

            result: ResponseT = await self.client.expire(name=key, time=time)

            self._logger.debug(
                msg="Key expiration set in Redis",
                extra={"key": key, "success": result},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to set key expiration in Redis: {exc!s}",
                extra={"key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return result

    async def ttl(self, key: str) -> int:
        """Get Key Time-To-Live.

        Arguments:
            key (str): Redis key.

        Returns:
            int: TTL in seconds (-1 if no expiration, -2 if key does not exist).

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(msg="Getting key TTL from Redis", extra={"key": key})

            ttl_value: ResponseT = await self.client.ttl(name=key)

            self._logger.debug(
                msg="Key TTL retrieved from Redis",
                extra={"key": key, "ttl": ttl_value},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get key TTL from Redis: {exc!s}",
                extra={"key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return ttl_value

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment Key Value.

        Arguments:
            key (str): Redis key.
            amount (int): Increment amount (default: 1).

        Returns:
            int: New value after increment.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Incrementing key value in Redis",
                extra={"key": key, "amount": amount},
            )

            new_value: ResponseT = await self.client.incrby(name=key, amount=amount)

            self._logger.debug(
                msg="Key value incremented in Redis",
                extra={"key": key, "new_value": new_value},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to increment key value in Redis: {exc!s}",
                extra={"key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return new_value

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement Key Value.

        Arguments:
            key (str): Redis key.
            amount (int): Decrement amount (default: 1).

        Returns:
            int: New value after decrement.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Decrementing key value in Redis",
                extra={"key": key, "amount": amount},
            )

            new_value: ResponseT = await self.client.decrby(name=key, amount=amount)

            self._logger.debug(
                msg="Key value decremented in Redis",
                extra={"key": key, "new_value": new_value},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to decrement key value in Redis: {exc!s}",
                extra={"key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return new_value

    async def hget(self, name: str, key: str) -> str | None:
        """Get Hash Field Value.

        Arguments:
            name (str): Hash name.
            key (str): Field key.

        Returns:
            str | None: Field value if exists, None otherwise.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Getting hash field value from Redis",
                extra={"hash_name": name, "field_key": key},
            )

            value: str | None = await self.client.hget(name=name, key=key)  # ty:ignore[invalid-await]

            self._logger.debug(
                msg="Hash field value retrieved from Redis",
                extra={"hash_name": name, "field_key": key, "value_exists": value is not None},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get hash field value from Redis: {exc!s}",
                extra={"hash_name": name, "field_key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return value

    async def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict[str, str] | None = None,
    ) -> int:
        """Set Hash Field Value.

        Arguments:
            name (str): Hash name.
            key (str | None): Field key.
            value (str | None): Field value.
            mapping (dict[str, str] | None): Multiple field-value pairs.

        Returns:
            int: Number of fields added.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Setting hash field value in Redis",
                extra={"hash_name": name, "field_key": key, "has_mapping": mapping is not None},
            )

            count: int = await self.client.hset(name=name, key=key, value=value, mapping=mapping)  # ty:ignore[invalid-await]

            self._logger.debug(
                msg="Hash field value set in Redis",
                extra={"hash_name": name, "fields_added": count},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to set hash field value in Redis: {exc!s}",
                extra={"hash_name": name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return count

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get All Hash Fields.

        Arguments:
            name (str): Hash name.

        Returns:
            dict[str, str]: All field-value pairs.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(msg="Getting all hash fields from Redis", extra={"hash_name": name})

            fields: dict = await self.client.hgetall(name=name)  # ty:ignore[invalid-await]

            self._logger.debug(
                msg="All hash fields retrieved from Redis",
                extra={"hash_name": name, "field_count": len(fields)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get all hash fields from Redis: {exc!s}",
                extra={"hash_name": name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return fields

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete Hash Field(s).

        Arguments:
            name (str): Hash name.
            *keys (str): Field keys to delete.

        Returns:
            int: Number of fields deleted.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Deleting hash fields from Redis",
                extra={"hash_name": name, "field_keys": keys},
            )

            count: int = await self.client.hdel(name, *keys)  # ty:ignore[invalid-await]

            self._logger.debug(
                msg="Hash fields deleted from Redis",
                extra={"hash_name": name, "deleted_count": count},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete hash fields from Redis: {exc!s}",
                extra={"hash_name": name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return count

    async def hexists(self, name: str, key: str) -> bool:
        """Check If Hash Field Exists.

        Arguments:
            name (str): Hash name.
            key (str): Field key.

        Returns:
            bool: True if field exists, False otherwise.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Checking hash field existence in Redis",
                extra={"hash_name": name, "field_key": key},
            )

            exists: bool = await self.client.hexists(name=name, key=key)  # ty:ignore[invalid-await]

            self._logger.debug(
                msg="Hash field existence checked in Redis",
                extra={"hash_name": name, "field_key": key, "exists": exists},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to check hash field existence in Redis: {exc!s}",
                extra={"hash_name": name, "field_key": key, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return exists

    async def execute_pipeline(self, commands: list[tuple[str, tuple[Any, ...]]]) -> list[Any]:
        """Execute Redis Pipeline.

        Arguments:
            commands (list[tuple[str, tuple[Any, ...]]]): List of (method_name, args) tuples.

        Returns:
            list[Any]: Results of pipeline execution.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Executing Redis pipeline",
                extra={"command_count": len(commands)},
            )

            async with self.client.pipeline() as pipe:
                for method_name, args in commands:
                    method = getattr(pipe, method_name)
                    method(*args)

                results = await pipe.execute()

            self._logger.debug(
                msg="Redis pipeline executed successfully",
                extra={"command_count": len(commands), "result_count": len(results)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to execute Redis pipeline: {exc!s}",
                extra={"command_count": len(commands), "exception_type": type(exc).__name__},
            )
            raise

        else:
            return results

    async def scan_keys(self, pattern: str = "*", count: int = 1000) -> list[str]:
        """Scan Keys With Pattern.

        Arguments:
            pattern (str): Key pattern to match (default: "*").
            count (int): Number of keys to return per iteration (default: 1000).

        Returns:
            list[str]: List of matching keys.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Scanning keys in Redis",
                extra={"pattern": pattern, "count": count},
            )

            keys: list[str] = []
            cursor = 0

            while True:
                cursor, batch_keys = await self.client.scan(cursor=cursor, match=pattern, count=count)
                keys.extend(batch_keys)

                if cursor == 0:
                    break

            self._logger.debug(
                msg="Keys scanned in Redis",
                extra={"pattern": pattern, "total_keys": len(keys)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to scan keys in Redis: {exc!s}",
                extra={"pattern": pattern, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return keys

    async def get_info(self, section: str | None = None) -> dict[str, Any]:
        """Get Redis Server Info.

        Arguments:
            section (str | None): Info section to retrieve (default: all).

        Returns:
            dict[str, Any]: Redis server information.

        Raises:
            RedisError: If Redis operation fails.
        """

        try:
            self._logger.debug(
                msg="Getting Redis server info",
                extra={"section": section},
            )

            info: ResponseT = await self.client.info(section=section)

            self._logger.debug(
                msg="Redis server info retrieved",
                extra={"section": section, "info_keys": len(info)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get Redis server info: {exc!s}",
                extra={"section": section, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return info

    def _create_connection_pool(self) -> ConnectionPool:
        """Create Redis Connection Pool.

        Arguments:
            None

        Returns:
            ConnectionPool: Redis connection pool instance.

        Raises:
            None
        """

        redis_url: str = self._build_redis_url()

        pool: ConnectionPool = ConnectionPool.from_url(
            url=redis_url,
            max_connections=settings.redis_max_connections,
            retry_on_timeout=settings.redis_retry_on_timeout,
            socket_keepalive=settings.redis_socket_keepalive,
            socket_keepalive_options=settings.redis_socket_keepalive_options,
            health_check_interval=settings.redis_health_check_interval,
            decode_responses=settings.redis_decode_responses,
            encoding=settings.redis_encoding,
        )

        self._logger.debug(
            msg="Redis connection pool created",
            extra={
                "max_connections": settings.redis_max_connections,
                "health_check_interval": settings.redis_health_check_interval,
            },
        )

        return pool

    def _build_redis_url(self) -> str:
        """Build Redis Connection URL.

        Arguments:
            None

        Returns:
            str: Redis connection URL.

        Raises:
            None
        """

        scheme: Literal["rediss", "redis"] = "rediss" if settings.redis_ssl else "redis"
        auth_part = ""

        if settings.redis_username and settings.redis_password:
            auth_part = f"{settings.redis_username}:{settings.redis_password}@"
        elif settings.redis_password:
            auth_part = f":{settings.redis_password}@"

        redis_url = (
            f"{scheme}://{auth_part}{settings.redis_host}:{settings.redis_port}/{settings.redis_database}"
            f"?socket_connect_timeout={settings.redis_connection_timeout}"
            f"&socket_timeout={settings.redis_socket_timeout}"
        )

        if settings.redis_ssl and not settings.redis_ssl_verify:
            redis_url += "&ssl_cert_reqs=none"

        self._logger.debug(
            msg="Redis connection URL built",
            extra={
                "scheme": scheme,
                "host": settings.redis_host,
                "port": settings.redis_port,
                "database": settings.redis_database,
            },
        )

        return redis_url


redis_adapter: RedisAdapter | None = None


async def get_redis_adapter() -> RedisAdapter:
    """Get Redis Adapter Instance.

    Arguments:
        None

    Returns:
        RedisAdapter: Redis adapter instance.

    Raises:
        RuntimeError: If Redis is not enabled.
    """

    global redis_adapter  # noqa: PLW0603

    if not settings.redis_enabled:
        msg = "Redis is not enabled in settings"
        raise RuntimeError(msg)

    if redis_adapter is None:
        redis_adapter = RedisAdapter()

    return redis_adapter


async def initialize_redis() -> RedisAdapter | None:
    """Initialize Redis Connection.

    Arguments:
        None

    Returns:
        RedisAdapter | None: Redis adapter instance if enabled, None otherwise.

    Raises:
        None
    """

    if not settings.redis_enabled:
        logger: logging.Logger = get_logger(name="redis.initialize")
        logger.info(msg="Redis is disabled")
        return None

    logger: logging.Logger = get_logger(name="redis.initialize")

    try:
        adapter: RedisAdapter = await get_redis_adapter()
        await adapter.connect()

        is_healthy: bool = await adapter.health_check()
        if not is_healthy:
            logger.warning(msg="Redis health check failed")
            return None

        logger.info(msg="Redis initialization successful")

    except Exception as exc:
        logger.warning(
            msg=f"Failed to initialize Redis (service will continue without Redis): {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    else:
        return adapter


async def shutdown_redis() -> None:
    """Shutdown Redis Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global redis_adapter  # noqa: PLW0603

    if redis_adapter is not None:
        try:
            await redis_adapter.disconnect()
            redis_adapter = None

        except Exception as exc:
            logger: logging.Logger = get_logger(name="redis.shutdown")
            logger.warning(
                msg=f"Error during Redis shutdown: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )


__all__: list[str] = [
    "RedisAdapter",
    "get_redis_adapter",
    "initialize_redis",
    "shutdown_redis",
]
