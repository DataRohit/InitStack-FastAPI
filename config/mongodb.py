# Standard Library Imports
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# Third-Party Imports
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.errors import PyMongoError

# Local Imports
from config.settings import settings


# MongoDB Client Manager
class MongoDBManager:
    """
    MongoDB Connection Manager

    This Class Manages MongoDB Connections Using PyMongo's Async Client.
    Requires PyMongo 4.0+ with Async Support.

    Attributes:
        client (AsyncMongoClient): Async MongoDB Client
        db (AsyncDatabase): Database Instance
    """

    # Initialize MongoDB Manager
    def __init__(self) -> None:
        """
        Initialize MongoDB Manager with Connection Settings
        """

        # Initialize MongoDB Client
        self.client: AsyncMongoClient = AsyncMongoClient(
            settings.MONGODB_URI,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=100,
            minPoolSize=10,
        )

        # Initialize Database
        self.db: AsyncDatabase = self.client[settings.MONGODB_DATABASE]

    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator:
        """
        Get Database Connection Context Manager

        Provides Async Context Manager for MongoDB Database Access.

        Yields:
            AsyncDatabase: Configured Database Instance

        Raises:
            PyMongoError: If Connection Fails
        """

        try:
            # Ping MongoDB to verify connection
            await self.client.admin.command("ping")

            # Yield Database Instance
            yield self.db

        except PyMongoError as e:
            # Raise PyMongoError with Custom Message
            msg: str = f"MongoDB Operation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e

        finally:
            # Connection Pooling Handled by PyMongo
            pass


# Initialize MongoDB Manager
mongodb_manager: MongoDBManager = MongoDBManager()


# Get Database Helper
@asynccontextmanager
async def get_mongodb() -> AsyncGenerator:
    """
    Get MongoDB Database Helper

    Convenience Function for Accessing MongoDB Database.

    Yields:
        AsyncDatabase: Configured Database Instance
    """

    # Get Database Connection
    async with mongodb_manager.get_db() as db:
        # Yield Database Instance
        yield db


# Exports
__all__: list[str] = ["get_mongodb", "mongodb_manager"]
