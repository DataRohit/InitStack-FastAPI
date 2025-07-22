# Standard Library Imports
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

# Third-Party Imports
from redis.asyncio import Redis
from redis.exceptions import RedisError

# Local Imports
from config.settings import settings


# Redis Client Manager
class RedisManager:
    """
    Redis Connection Manager

    This Class Manages Redis Connections Using redis-py's Async Client.
    Supports Multiple Databases Through Connection Pooling.

    Attributes:
        pool (ConnectionPool): Redis Connection Pool
    """

    # Get Redis Client Context Manager
    @asynccontextmanager
    async def get_client(self, db: int = 0) -> AsyncGenerator:
        """
        Get Redis Client Context Manager

        Args:
            db (int): Redis Database Number (default: 0)

        Yields:
            Redis: Configured Redis Client Instance

        Raises:
            RedisError: If Connection Fails
        """

        # Initialize Redis Client
        client: Redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=db,
            password=settings.REDIS_PASS,
            decode_responses=True,
        )

        try:
            # Verify Connection
            await client.ping()

            # Yield Client
            yield client

        except RedisError as e:
            # Set Error Message
            msg: str = f"Redis Operation Failed: {e!s}"

            # Raise RedisError
            raise RedisError(msg) from e

        finally:
            # Close Client
            await client.close()

    # Get Value from Redis
    async def get(self, key: str, db: int = 0) -> Any | None:
        """
        Get Value from Redis

        Args:
            key (str): Key to Retrieve
            db (int): Redis Database Number (default: 0)

        Returns:
            Any | None: Retrieved Value or None
        """

        # With Client
        async with self.get_client(db=db) as client:
            # Get Value
            return await client.get(key)

    # Set Value in Redis
    async def set(self, key: str, value: Any, expire: int | None = None, db: int = 0) -> bool:
        """
        Set Value in Redis

        Args:
            key (str): Key to Set
            value (Any): Value to Store
            expire (int | None): Expiration in Seconds
            db (int): Redis Database Number (default: 0)

        Returns:
            bool: True if successful
        """

        # With Client
        async with self.get_client(db=db) as client:
            # Set Value
            return await client.set(key, value, ex=expire)

    # Delete Key from Redis
    async def delete(self, key: str, db: int = 0) -> bool:
        """
        Delete Key from Redis

        Args:
            key (str): Key to Delete
            db (int): Redis Database Number (default: 0)

        Returns:
            bool: True if Key was Deleted
        """

        # With Client
        async with self.get_client(db=db) as client:
            # Delete Key
            return await client.delete(key) > 0


# Initialize Redis Manager
redis_manager: RedisManager = RedisManager()


# Exports
__all__: list[str] = ["redis_manager"]
