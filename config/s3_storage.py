# Standard Library Imports
from collections.abc import Generator
from contextlib import contextmanager

# Third-Party Imports
import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

# Local Imports
from config.settings import settings


# S3 Client Manager
class S3Manager:
    """
    S3 Connection Manager

    This Class Manages S3 Connections Using Boto3 Client.
    Compatible with Both AWS S3 and MinIO Storage.

    Attributes:
        sync_client (BaseClient | None): Synchronous S3 Client
        async_client (BaseClient | None): Async S3 Client
    """

    # Initialize S3 Manager
    def __init__(self) -> None:
        """
        Initialize S3 Manager with Connection Settings
        """

        # Initialize Connection Attributes
        self.sync_client: BaseClient | None = None
        self.async_client: BaseClient | None = None

        # Initialize Connections Lazily to Avoid Circular Import Issues
        self._initialized: bool = False

    # Initialize S3 Connections Lazily
    def _initialize_connections(self) -> None:
        """
        Initialize S3 Connections Lazily to Avoid Circular Import Issues

        This Method Creates S3 Client Connections Only When First Needed.
        Helps Avoid Circular Import Issues That Can Occur During Module Loading.
        """

        # If Already Initialized
        if self._initialized:
            # Return
            return

        try:
            # Connection Configuration
            s3_config: Config = Config(
                region_name=settings.MINIO_REGION,
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "standard"},
            )

            # Initialize S3 Sync Client
            self.sync_client: BaseClient = boto3.client(
                "s3",
                endpoint_url=f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}",
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                config=s3_config,
            )

            # Mark as Initialized
            self._initialized: bool = True

        except Exception as e:
            # Set Error Message
            msg: str = f"Failed to Initialize S3 Connections: {e!s}"

            # Raise ClientError
            raise ClientError(msg) from e

    # Health Check Method
    def health_check(self) -> bool:
        """
        Perform S3 Health Check

        Verifies Connection to S3/MinIO by Listing Buckets.
        Returns True If Connection is Successful.

        Returns:
            bool: True if connection is healthy, False otherwise

        Raises:
            ClientError: If Connection Fails
        """

        # Initialize Connections If Needed
        self._initialize_connections()

        try:
            # List Buckets to Test Connection
            self.sync_client.get_paginator("list_buckets").paginate()

        except ClientError as e:
            # Set Error Message
            msg: str = f"S3 Health Check Failed: {e!s}"

            # Raise ClientError
            raise ClientError(msg) from e

        # Return Success
        return True

    # Get Synchronous Client Context Manager
    @contextmanager
    def get_sync_client(self) -> Generator:
        """
        Get Synchronous S3 Client Context Manager

        Provides Synchronous Context Manager for S3 Client Access

        Yields:
            BaseClient: Configured S3 Client Instance
        """

        # Initialize Connections If Needed
        self._initialize_connections()

        try:
            # Yield Sync Client
            yield self.sync_client

        except ClientError as e:
            # Set Error Message
            msg: str = f"S3 Operation Failed: {e!s}"

            # Raise ClientError
            raise ClientError(msg) from e


# Initialize S3 Manager Singleton Instance
_s3_manager: S3Manager | None = None


def get_s3_manager() -> S3Manager:
    """
    Get S3 Manager Instance Using Singleton Pattern

    Returns the Same S3 Manager Instance Across All Calls
    to Ensure Connection Reuse and Resource Efficiency.

    Returns:
        S3Manager: The S3 Manager Instance
    """

    # Access Global Variable
    global _s3_manager  # noqa: PLW0603

    # If Manager Not Initialized
    if _s3_manager is None:
        # Create New Instance
        _s3_manager = S3Manager()

    # Return Manager Instance
    return _s3_manager


@contextmanager
def get_sync_s3() -> Generator:
    """
    Get Synchronous S3 Client Helper

    Convenience Function for Accessing S3 Client Using
    Synchronous Context Manager Pattern.

    Yields:
        BaseClient: Configured S3 Client Instance
    """

    # Get S3 Manager Instance
    manager: S3Manager = get_s3_manager()

    # Get Client Via Context Manager
    with manager.get_sync_client() as client:
        # Yield Client
        yield client


# Exports
__all__: list[str] = ["S3Manager", "get_s3_manager", "get_sync_s3"]
