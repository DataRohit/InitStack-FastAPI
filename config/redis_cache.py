# Standard Library Imports
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

# Third-Party Imports
from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

# Local Imports
from config.settings import settings


# Redis Client Manager
class RedisManager:
    """
    Redis Connection Manager

    This Class Manages Redis Connections Using redis-py's Client.
    Supports Both Synchronous and Asynchronous Operations.

    Attributes:
        sync_client (SyncRedis | None): Synchronous Redis Client
        async_client (AsyncRedis | None): Async Redis Client
    """

    # Initialize Redis Manager
    def __init__(self) -> None:
        """
        Initialize Redis Manager with Connection Settings
        """

        # Initialize Connection Attributes
        self.sync_client: SyncRedis | None = None
        self.async_client: AsyncRedis | None = None

        # Initialize Connections Lazily to Avoid Circular Import Issues
        self._initialized: bool = False

    # Initialize Redis Connections Lazily
    def _initialize_connections(self) -> None:
        """
        Initialize Redis Connections Lazily to Avoid Circular Import Issues

        This Method Creates Redis Client Connections Only When First Needed.
        Helps Avoid Circular Import Issues That Can Occur During Module Loading.
        """

        # If Already Initialized
        if self._initialized:
            # Return
            return

        try:
            # Connection Parameters
            connection_params = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "password": settings.REDIS_PASS,
                "decode_responses": True,
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "retry_on_timeout": True,
                "max_connections": 100,
            }

            # Initialize Sync Redis Client
            self.sync_client = SyncRedis(**connection_params)

            # Initialize Async Redis Client
            self.async_client = AsyncRedis(**connection_params)

            # Mark as Initialized
            self._initialized = True

        except Exception as e:
            # Set Error Message
            msg: str = f"Failed to Initialize Redis Connections: {e!s}"

            # Raise RedisError
            raise RedisError(msg) from e

    # Health Check Method
    def health_check(self) -> bool:
        """
        Perform Redis Health Check

        Verifies Connection to Redis by Pinging the Server.
        Returns True If Connection is Successful.

        Returns:
            bool: True if connection is healthy, False otherwise

        Raises:
            RedisError: If Connection Fails
        """

        # Initialize Connections If Needed
        self._initialize_connections()

        try:
            # Ping Redis Server
            return self.sync_client.ping()

        except RedisError as e:
            # Set Error Message
            msg: str = f"Redis Health Check Failed: {e!s}"

            # Raise RedisError
            raise RedisError(msg) from e

    # Get Asynchronous Client Context Manager
    @asynccontextmanager
    async def get_async_client(self, db: int = 0) -> AsyncGenerator:
        """
        Get Asynchronous Redis Client Context Manager

        Args:
            db (int): Redis Database Number (default: 0)

        Yields:
            AsyncRedis: Configured Async Redis Client Instance

        Raises:
            RedisError: If Connection Fails
        """

        # Initialize Connections If Needed
        self._initialize_connections()

        try:
            # Verify Connection
            await self.async_client.ping()

            # Select Database
            self.async_client.connection_pool.connection_kwargs["db"] = db

            # Yield Client
            yield self.async_client

        except RedisError as e:
            # Set Error Message
            msg: str = f"Redis Operation Failed: {e!s}"

            # Raise RedisError
            raise RedisError(msg) from e

    # Get Synchronous Client Context Manager
    @contextmanager
    def get_sync_client(self, db: int = 0) -> Generator:
        """
        Get Synchronous Redis Client Context Manager

        Args:
            db (int): Redis Database Number (default: 0)

        Yields:
            SyncRedis: Configured Sync Redis Client Instance

        Raises:
            RedisError: If Connection Fails
        """

        # Initialize Connections If Needed
        self._initialize_connections()

        try:
            # Verify Connection
            self.sync_client.ping()

            # Select Database
            self.sync_client.connection_pool.connection_kwargs["db"] = db

            # Yield Client
            yield self.sync_client

        except RedisError as e:
            # Set Error Message
            msg: str = f"Redis Operation Failed: {e!s}"

            # Raise RedisError
            raise RedisError(msg) from e


# Initialize Redis Manager Singleton Instance
_redis_manager: RedisManager | None = None


def get_redis_manager() -> RedisManager:
    """
    Get Redis Manager Instance Using Singleton Pattern

    Returns the Same Redis Manager Instance Across All Calls
    to Ensure Connection Reuse and Resource Efficiency.

    Returns:
        RedisManager: The Redis Manager Instance
    """

    # Access Global Variable
    global _redis_manager  # noqa: PLW0603

    # If Manager Not Initialized
    if _redis_manager is None:
        # Create New Instance
        _redis_manager = RedisManager()

    # Return Manager Instance
    return _redis_manager


@contextmanager
def get_sync_redis(db: int = 0) -> Generator:
    """
    Get Synchronous Redis Client Helper

    Convenience Function for Accessing Redis Client Using
    Synchronous Context Manager Pattern.

    Args:
        db (int): Redis Database Number (default: 0)

    Yields:
        SyncRedis: Configured Sync Redis Client Instance
    """

    # Get Redis Manager Instance
    manager: RedisManager = get_redis_manager()

    # Get Client Via Context Manager
    with manager.get_sync_client(db=db) as client:
        # Yield Client
        yield client


@asynccontextmanager
async def get_async_redis(db: int = 0) -> AsyncGenerator:
    """
    Get Asynchronous Redis Client Helper

    Convenience Function for Accessing Redis Client Using
    Asynchronous Context Manager Pattern.

    Args:
        db (int): Redis Database Number (default: 0)

    Yields:
        AsyncRedis: Configured Async Redis Client Instance
    """

    # Get Redis Manager Instance
    manager: RedisManager = get_redis_manager()

    # Get Client Via Context Manager
    async with manager.get_async_client(db=db) as client:
        # Yield Client
        yield client


# Initialize Redis Manager Instance
redis_manager: RedisManager = get_redis_manager()


# Exports
__all__: list[str] = ["RedisManager", "get_async_redis", "get_redis_manager", "get_sync_redis", "redis_manager"]
