# Standard Library Imports
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

# Third-Party Imports
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError
from pymongo.mongo_client import MongoClient

# Local Imports
from config.settings import settings


# MongoDB Client Manager
class MongoDBManager:
    """
    MongoDB Connection Manager

    This Class Manages MongoDB Connections Using PyMongo's Async Client.
    Requires PyMongo 4.0+ with Async Support.

    Attributes:
        sync_client (MongoClient): Synchronous MongoDB Client
        async_client (AsyncMongoClient): Async MongoDB Client
        sync_db (Database): Synchronous Database Instance
        async_db (AsyncDatabase): Async Database Instance
    """

    # Initialize MongoDB Manager
    def __init__(self) -> None:
        """
        Initialize MongoDB Manager with Connection Settings
        """

        # Initialize MongoDB Sync Client
        self.sync_client: MongoClient = MongoClient(
            settings.MONGODB_URI,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=100,
            minPoolSize=10,
        )

        # Initialize MongoDB Async Client
        self.async_client: AsyncMongoClient = AsyncMongoClient(
            settings.MONGODB_URI,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=100,
            minPoolSize=10,
        )

        # Initialize Database
        self.sync_db: Database = self.sync_client[settings.MONGODB_DATABASE]
        self.async_db: AsyncDatabase = self.async_client[settings.MONGODB_DATABASE]

    # Get Synchronous Database Connection Context Manager
    @contextmanager
    def get_sync_db(self):
        """
        Get Synchronous Database Connection Context Manager

        Provides Synchronous Context Manager for MongoDB Database Access.

        Yields:
            Database: Configured Database Instance

        Raises:
            PyMongoError: If Connection Fails
        """

        try:
            # Yield Database Instance
            yield self.sync_db

        except PyMongoError as e:
            # Raise PyMongoError with Custom Message
            msg: str = f"MongoDB Operation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

        finally:
            # Connection Pooling Handled by PyMongo
            pass

    # Get Asynchronous Database Connection Context Manager
    @asynccontextmanager
    async def get_async_db(self):
        """
        Get Asynchronous Database Connection Context Manager

        Provides Asynchronous Context Manager for MongoDB Database Access.

        Yields:
            AsyncDatabase: Configured Database Instance

        Raises:
            PyMongoError: If Connection Fails
        """

        try:
            # Yield Database Instance
            yield self.async_db

        except PyMongoError as e:
            # Raise PyMongoError with Custom Message
            msg: str = f"MongoDB Operation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

        finally:
            # Connection Pooling Handled by PyMongo
            pass

    # Close All Connections
    async def close_all(self) -> None:
        """
        Close All MongoDB Connections
        """

        # Close Synchronous Client
        self.sync_client.close()

        # Close Asynchronous Client
        await self.async_client.close()


# Initialize MongoDB Manager
mongodb_manager: MongoDBManager = MongoDBManager()


# Get Synchronous Database Helper
@contextmanager
def get_sync_mongodb() -> Generator:
    """
    Get Synchronous MongoDB Database Helper

    Convenience Function for Accessing MongoDB Database.

    Yields:
        Database: Configured Database Instance
    """

    # Get Synchronous Database Connection
    with mongodb_manager.get_sync_db() as db:
        # Yield Database Instance
        yield db


# Get Asynchronous Database Helper
@asynccontextmanager
async def get_async_mongodb() -> AsyncGenerator:
    """
    Get Asynchronous MongoDB Database Helper

    Convenience Function for Accessing MongoDB Database.

    Yields:
        AsyncDatabase: Configured Database Instance
    """

    # Get Asynchronous Database Connection
    async with mongodb_manager.get_async_db() as db:
        # Yield Database Instance
        yield db


# Exports
__all__: list[str] = ["get_async_mongodb", "get_sync_mongodb", "mongodb_manager"]
