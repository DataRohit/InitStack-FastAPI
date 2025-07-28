# Standard Library Imports
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

# Third-Party Imports
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError
from pymongo.synchronous.database import Database
from pymongo.synchronous.mongo_client import MongoClient

# Local Imports
from config.settings import settings


# MongoDB Client Manager
class MongoDBManager:
    """
    MongoDB Connection Manager

    This Class Manages MongoDB Connections Using PyMongo's Async Client.
    Requires PyMongo 4.0+ with Async Support.

    Attributes:
        sync_client (MongoClient | None): Synchronous MongoDB Client
        async_client (AsyncMongoClient | None): Async MongoDB Client
        sync_db (Database | None): Synchronous Database Instance
        async_db (AsyncDatabase | None): Async Database Instance
    """

    # Initialize MongoDB Manager
    def __init__(self) -> None:
        """
        Initialize MongoDB Manager with Connection Settings
        """

        # Initialize Connection Attributes
        self.sync_client: MongoClient | None = None
        self.async_client: AsyncMongoClient | None = None
        self.sync_db: Database | None = None
        self.async_db: AsyncDatabase | None = None

        # Initialize Connections Lazily to Avoid Circular Import Issues
        self._initialized = False

    # Initialize MongoDB Connections Lazily
    def _initialize_connections(self) -> None:
        """
        Initialize MongoDB Connections Lazily to Avoid Circular Import Issues

        This Method Creates MongoDB Client Connections Only When First Needed.
        Helps Avoid Circular Import Issues That Can Occur During Module Loading.
        """

        # If Already Initialized
        if self._initialized:
            # Return
            return

        try:
            # Connection Settings
            connection_params = {
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 30000,
                "serverSelectionTimeoutMS": 5000,
                "maxPoolSize": 100,
                "minPoolSize": 10,
                "retryWrites": True,
                "retryReads": True,
                "maxIdleTimeMS": 300000,  # 5 Minutes
                "waitQueueTimeoutMS": 10000,
            }

            # Initialize MongoDB Sync Client
            self.sync_client = MongoClient(settings.MONGODB_URI, **connection_params)

            # Initialize MongoDB Async Client
            self.async_client = AsyncMongoClient(settings.MONGODB_URI, **connection_params)

            # Initialize Database Instances
            self.sync_db = self.sync_client[settings.MONGODB_DATABASE]
            self.async_db = self.async_client[settings.MONGODB_DATABASE]

            # Mark as Initialized
            self._initialized = True

        except Exception as e:
            # Set Error Message
            msg: str = f"Failed to Initialize MongoDB Connections: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

    # Get Synchronous Database Connection Context Manager
    @contextmanager
    def get_sync_db(self) -> Generator:
        """
        Get Synchronous Database Connection Context Manager

        Provides Synchronous Context Manager for MongoDB Database Access
        with Automatic Connection Recovery and Error Handling.

        Yields:
            Database: Configured Database Instance

        Raises:
            PyMongoError: If Connection Fails or Database Not Available
        """

        # If Not Initialized
        if not self._initialized:
            # Initialize Connections
            self._initialize_connections()

        # If Database Connection is Not Available
        if self.sync_db is None:
            # Set Error Message
            msg: str = "Sync Database Connection Not Initialized"

            # Raise PyMongoError
            raise PyMongoError(msg)

        try:
            # Test Connection with Ping Command
            self.sync_client.admin.command("ping")

            # Yield Database Instance
            yield self.sync_db

        except (ConnectionFailure, ServerSelectionTimeoutError):
            # Try to Reinitialize Connection on Connection Failure
            self._initialized = False
            self._initialize_connections()

            # Yield Database Instance After Reinitialization
            yield self.sync_db

        except PyMongoError as e:
            # Set Error Message
            msg: str = f"MongoDB Operation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

    # Get Asynchronous Database Connection Context Manager
    @asynccontextmanager
    async def get_async_db(self) -> AsyncGenerator:
        """
        Get Asynchronous Database Connection Context Manager

        Provides Asynchronous Context Manager for MongoDB Database Access
        with Automatic Connection Recovery and Error Handling.

        Yields:
            AsyncDatabase: Configured Database Instance

        Raises:
            PyMongoError: If Connection Fails or Database Not Available
        """

        # If Not Initialized
        if not self._initialized:
            # Initialize Connections
            self._initialize_connections()

        # If Database Connection is Not Available
        if self.async_db is None:
            # Set Error Message
            msg: str = "Async Database Connection Not Initialized"

            # Raise PyMongoError
            raise PyMongoError(msg)

        try:
            # Test Connection with Ping Command
            await self.async_client.admin.command("ping")

            # Yield Database Instance
            yield self.async_db

        except (ConnectionFailure, ServerSelectionTimeoutError):
            # Try to Reinitialize Connection on Connection Failure
            self._initialized = False
            self._initialize_connections()

            # Yield Database Instance After Reinitialization
            yield self.async_db

        except PyMongoError as e:
            # Set Error Message
            msg: str = "MongoDB Operation Failed"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

    # Perform Synchronous Health Check
    def sync_health_check(self) -> bool:
        """
        Perform Synchronous Health Check on MongoDB Connection

        Tests MongoDB Connection Using Ping Command to Verify
        Database Connectivity and Availability.

        Returns:
            bool: True if Connection is Healthy, False Otherwise
        """

        try:
            # If Not Initialized
            if not self._initialized:
                # Initialize Connections
                self._initialize_connections()

            # Test Connection with Ping Command
            self.sync_client.admin.command("ping")

        except Exception:
            # Return Failure
            return False

        # Return Success
        return True

    # Perform Asynchronous Health Check
    async def async_health_check(self) -> bool:
        """
        Perform Asynchronous Health Check on MongoDB Connection

        Tests MongoDB Connection Using Ping Command to Verify
        Database Connectivity and Availability.

        Returns:
            bool: True if Connection is Healthy, False Otherwise
        """

        try:
            # If Not Initialized
            if not self._initialized:
                # Initialize Connections
                self._initialize_connections()

            # Test Connection with Ping Command
            await self.async_client.admin.command("ping")

        except Exception:
            # Return Failure
            return False

        # Return Success
        return True

    # Reset Connection State
    def reset_connections(self) -> None:
        """
        Reset Connection State to Force Reinitialization

        Useful for Worker Processes That Need Fresh Connections.
        Forces the Manager to Create New Connection Instances on Next Access.
        """

        # Reset Initialization Flag
        self._initialized = False

        # Clear Connection References
        self.sync_client = None
        self.async_client = None
        self.sync_db = None
        self.async_db = None

    # Close All MongoDB Connections
    async def close_all(self) -> None:
        """
        Close All MongoDB Connections

        Properly Closes Both Synchronous and Asynchronous MongoDB Client
        Connections and Resets Connection State.
        """

        try:
            # If Synchronous Client is Available
            if self.sync_client:
                # Close Synchronous Client
                self.sync_client.close()

            # If Asynchronous Client is Available
            if self.async_client:
                # Close Asynchronous Client
                await self.async_client.close()

        except Exception:  # noqa: S110
            # Ignore Errors During Cleanup
            pass

        finally:
            # Reset Connection State
            self._initialized = False
            self.sync_client = None
            self.async_client = None
            self.sync_db = None
            self.async_db = None


# Initialize MongoDB Manager Singleton Instance
_mongodb_manager: MongoDBManager | None = None


# Get MongoDB Manager Instance
def get_mongodb_manager() -> MongoDBManager:
    """
    Get MongoDB Manager Instance Using Singleton Pattern

    Returns the Same MongoDB Manager Instance Across All Calls
    to Ensure Connection Reuse and Resource Efficiency.

    Returns:
        MongoDBManager: The MongoDB Manager Instance
    """

    # Access Global Manager Instance
    global _mongodb_manager  # noqa: PLW0603

    # If Not Initialized
    if _mongodb_manager is None:
        # Initialize Manager
        _mongodb_manager = MongoDBManager()

    # Return Manager Instance
    return _mongodb_manager


# Get Synchronous Database Helper
@contextmanager
def get_sync_mongodb() -> Generator:
    """
    Get Synchronous MongoDB Database Helper

    Convenience Function for Accessing MongoDB Database Using
    Synchronous Context Manager Pattern.

    Yields:
        Database: Configured Database Instance
    """

    # Get MongoDB Manager Instance
    manager = get_mongodb_manager()

    # Get Synchronous Database Connection
    with manager.get_sync_db() as db:
        # Yield Database Instance
        yield db


# Get Asynchronous Database Helper
@asynccontextmanager
async def get_async_mongodb() -> AsyncGenerator:
    """
    Get Asynchronous MongoDB Database Helper

    Convenience Function for Accessing MongoDB Database Using
    Asynchronous Context Manager Pattern.

    Yields:
        AsyncDatabase: Configured Database Instance
    """

    # Get MongoDB Manager Instance
    manager = get_mongodb_manager()

    # Get Asynchronous Database Connection
    async with manager.get_async_db() as db:
        # Yield Database Instance
        yield db


# Exports
__all__: list[str] = ["get_async_mongodb", "get_mongodb_manager", "get_sync_mongodb"]
