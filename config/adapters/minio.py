from datetime import timedelta
from io import BytesIO
from typing import TYPE_CHECKING
from typing import Any

from minio import Minio
from minio.error import S3Error

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from minio.datatypes import Bucket
    from minio.datatypes import Object
    from urllib3 import BaseHTTPResponse


class MinIOAdapter:
    """Professional Production-Grade MinIO S3 Storage Adapter.

    Inherits:
        object

    Attributes:
        _client (Minio): MinIO client instance.
        _logger (logging.Logger): Logger instance for MinIO operations.
        _is_connected (bool): Connection status flag.
        _bucket_name (str): Default bucket name.

    Properties:
        client: Get MinIO client instance.
        is_connected: Get connection status.
        bucket_name: Get default bucket name.

    Methods:
        connect: Establish MinIO connection.
        disconnect: Close MinIO connection.
        health_check: Perform MinIO health check.
        create_bucket: Create storage bucket.
        bucket_exists: Check if bucket exists.
        list_buckets: List all buckets.
        delete_bucket: Delete storage bucket.
        upload_object: Upload object to bucket.
        download_object: Download object from bucket.
        get_object: Get object as bytes.
        delete_object: Delete object from bucket.
        list_objects: List objects in bucket.
        object_exists: Check if object exists.
        get_object_metadata: Get object metadata.
        copy_object: Copy object within or between buckets.
        get_presigned_url: Get presigned URL for object.
    """

    def __init__(self) -> None:
        """Initialize MinIO Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="minio.adapter")
        self._client: Minio | None = None
        self._is_connected: bool = False
        self._bucket_name: str = settings.minio_bucket_name

        self._logger.info(
            msg="MinIO adapter initialized",
            extra={
                "minio_endpoint": settings.minio_endpoint,
                "minio_bucket": settings.minio_bucket_name,
                "minio_secure": settings.minio_secure,
                "minio_region": settings.minio_region,
            },
        )

    @property
    def client(self) -> Minio:
        """Get MinIO Client Instance.

        Arguments:
            None

        Returns:
            Minio: MinIO client instance.

        Raises:
            RuntimeError: If MinIO client is not connected.
        """

        if not self._client or not self._is_connected:
            msg = "MinIO client is not connected. Call connect() first."
            raise RuntimeError(msg)

        return self._client

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to MinIO, False otherwise.

        Raises:
            None
        """

        return self._is_connected

    @property
    def bucket_name(self) -> str:
        """Get Default Bucket Name.

        Arguments:
            None

        Returns:
            str: Default bucket name.

        Raises:
            None
        """

        return self._bucket_name

    async def connect(self) -> bool:
        """Establish MinIO Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="MinIO client is already connected")
                return True

            self._logger.info(msg="Establishing MinIO connection")

            self._client = Minio(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
                region=settings.minio_region,
            )

            buckets: list[Bucket] = self._client.list_buckets()
            self._is_connected = True

            self._logger.info(
                msg="MinIO connection established successfully",
                extra={
                    "minio_endpoint": settings.minio_endpoint,
                    "minio_bucket": settings.minio_bucket_name,
                    "buckets_count": len(buckets),
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish MinIO connection: {exc!s}",
                extra={
                    "minio_endpoint": settings.minio_endpoint,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close MinIO Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="MinIO client is not connected")
                return

            self._logger.info(msg="Closing MinIO connection")

            self._client = None
            self._is_connected = False

            self._logger.info(msg="MinIO connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing MinIO connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform MinIO Health Check.

        Arguments:
            None

        Returns:
            bool: True if MinIO is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing MinIO health check")

            buckets: list[Bucket] = self._client.list_buckets()  # ty:ignore[possibly-missing-attribute]
            is_healthy: bool = buckets is not None

            self._logger.debug(
                msg=f"MinIO health check completed: {'healthy' if is_healthy else 'unhealthy'}",
                extra={"buckets_count": len(buckets) if buckets else 0},
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"MinIO health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return is_healthy

    async def create_bucket(self, bucket_name: str | None = None) -> bool:
        """Create Storage Bucket.

        Arguments:
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bool: True if bucket created or already exists, False otherwise.

        Raises:
            S3Error: If bucket creation fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.info(msg="Creating bucket", extra={"bucket_name": bucket})

            if not self.client.bucket_exists(bucket_name=bucket):
                self.client.make_bucket(bucket_name=bucket, location=settings.minio_region)
                self._logger.info(msg="Bucket created successfully", extra={"bucket_name": bucket})
            else:
                self._logger.info(msg="Bucket already exists", extra={"bucket_name": bucket})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to create bucket: {exc!s}",
                extra={"bucket_name": bucket, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return True

    async def bucket_exists(self, bucket_name: str | None = None) -> bool:
        """Check If Bucket Exists.

        Arguments:
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bool: True if bucket exists, False otherwise.

        Raises:
            S3Error: If check fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.debug(msg="Checking bucket existence", extra={"bucket_name": bucket})

            exists: bool = self.client.bucket_exists(bucket_name=bucket)

            self._logger.debug(
                msg="Bucket existence checked",
                extra={"bucket_name": bucket, "exists": exists},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to check bucket existence: {exc!s}",
                extra={"bucket_name": bucket, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return exists

    async def list_buckets(self) -> list[str]:
        """List All Buckets.

        Arguments:
            None

        Returns:
            list[str]: List of bucket names.

        Raises:
            S3Error: If listing fails.
        """

        try:
            self._logger.debug(msg="Listing buckets")

            buckets: list[Bucket] = self.client.list_buckets()
            bucket_names: list[str] = [bucket.name for bucket in buckets]

            self._logger.debug(
                msg="Buckets listed successfully",
                extra={"buckets_count": len(bucket_names)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to list buckets: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise

        else:
            return bucket_names

    async def delete_bucket(self, bucket_name: str | None = None) -> bool:
        """Delete Storage Bucket.

        Arguments:
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bool: True if bucket deleted successfully.

        Raises:
            S3Error: If deletion fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.info(msg="Deleting bucket", extra={"bucket_name": bucket})

            self.client.remove_bucket(bucket_name=bucket)

            self._logger.info(msg="Bucket deleted successfully", extra={"bucket_name": bucket})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete bucket: {exc!s}",
                extra={"bucket_name": bucket, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return True

    async def upload_object(
        self,
        object_name: str,
        data: bytes | BytesIO,
        *,
        bucket_name: str | None = None,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str | list[str] | tuple[str]] | None = None,
    ) -> bool:
        """Upload Object To Bucket.

        Arguments:
            object_name (str): Object name/key.
            data (bytes | BytesIO): Object data.
            bucket_name (str | None): Bucket name (uses default if None).
            content_type (str): Content type.
            metadata (dict[str, str | list[str] | tuple[str]] | None): Object metadata.

        Returns:
            bool: True if upload successful.

        Raises:
            S3Error: If upload fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.info(
                msg="Uploading object",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            if isinstance(data, bytes):
                data_stream: BytesIO = BytesIO(initial_bytes=data)
                data_length: int = len(data)
            else:
                data_stream: BytesIO = data
                data_stream.seek(0, 2)
                data_length: int = data_stream.tell()
                data_stream.seek(0)

            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data_stream,
                length=data_length,
                content_type=content_type,
                metadata=metadata,
            )

            self._logger.info(
                msg="Object uploaded successfully",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "size_bytes": data_length,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to upload object: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def download_object(
        self,
        object_name: str,
        file_path: str,
        *,
        bucket_name: str | None = None,
    ) -> bool:
        """Download Object From Bucket.

        Arguments:
            object_name (str): Object name/key.
            file_path (str): Local file path to save.
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bool: True if download successful.

        Raises:
            S3Error: If download fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.info(
                msg="Downloading object",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            self.client.fget_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
            )

            self._logger.info(
                msg="Object downloaded successfully",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "file_path": file_path,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to download object: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def get_object(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> bytes:
        """Get Object As Bytes.

        Arguments:
            object_name (str): Object name/key.
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bytes: Object data.

        Raises:
            S3Error: If retrieval fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.debug(
                msg="Getting object",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            response: BaseHTTPResponse = self.client.get_object(bucket_name=bucket, object_name=object_name)
            data: bytes = response.read()
            response.close()
            response.release_conn()

            self._logger.debug(
                msg="Object retrieved successfully",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "size_bytes": len(data),
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get object: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return data

    async def delete_object(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> bool:
        """Delete Object From Bucket.

        Arguments:
            object_name (str): Object name/key.
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bool: True if deletion successful.

        Raises:
            S3Error: If deletion fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.info(
                msg="Deleting object",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            self.client.remove_object(bucket_name=bucket, object_name=object_name)

            self._logger.info(
                msg="Object deleted successfully",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete object: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def list_objects(
        self,
        *,
        bucket_name: str | None = None,
        prefix: str | None = None,
        recursive: bool = True,
    ) -> list[str]:
        """List Objects In Bucket.

        Arguments:
            bucket_name (str | None): Bucket name (uses default if None).
            prefix (str | None): Object name prefix filter.
            recursive (bool): List recursively.

        Returns:
            list[str]: List of object names.

        Raises:
            S3Error: If listing fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.debug(
                msg="Listing objects",
                extra={"bucket_name": bucket, "prefix": prefix, "recursive": recursive},
            )

            objects: list[Object] = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix,
                recursive=recursive,
            )
            object_names: list[str] = [obj.object_name for obj in objects]

            self._logger.debug(
                msg="Objects listed successfully",
                extra={"bucket_name": bucket, "objects_count": len(object_names)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to list objects: {exc!s}",
                extra={"bucket_name": bucket, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return object_names

    async def object_exists(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> bool:
        """Check If Object Exists.

        Arguments:
            object_name (str): Object name/key.
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            bool: True if object exists, False otherwise.

        Raises:
            None
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.debug(
                msg="Checking object existence",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            self.client.stat_object(bucket_name=bucket, object_name=object_name)
            exists: bool = True

            self._logger.debug(
                msg="Object exists",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

        except S3Error as exc:
            if exc.code == "NoSuchKey":
                exists = False
                self._logger.debug(
                    msg="Object does not exist",
                    extra={"bucket_name": bucket, "object_name": object_name},
                )
            else:
                self._logger.exception(
                    msg=f"Failed to check object existence: {exc!s}",
                    extra={
                        "bucket_name": bucket,
                        "object_name": object_name,
                        "exception_type": type(exc).__name__,
                    },
                )
                raise

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to check object existence: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        return exists

    async def get_object_metadata(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> dict[str, Any]:
        """Get Object Metadata.

        Arguments:
            object_name (str): Object name/key.
            bucket_name (str | None): Bucket name (uses default if None).

        Returns:
            dict[str, Any]: Object metadata.

        Raises:
            S3Error: If retrieval fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.debug(
                msg="Getting object metadata",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            stat: Object = self.client.stat_object(bucket_name=bucket, object_name=object_name)

            metadata: dict[str, Any] = {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
            }

            self._logger.debug(
                msg="Object metadata retrieved successfully",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get object metadata: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return metadata

    async def get_presigned_url(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
        expires_seconds: int = 3600,
    ) -> str:
        """Get Presigned URL For Object.

        Arguments:
            object_name (str): Object name/key.
            bucket_name (str | None): Bucket name (uses default if None).
            expires_seconds (int): URL expiration time in seconds.

        Returns:
            str: Presigned URL.

        Raises:
            S3Error: If URL generation fails.
        """

        bucket: str = bucket_name or self._bucket_name

        try:
            self._logger.debug(
                msg="Generating presigned URL",
                extra={"bucket_name": bucket, "object_name": object_name},
            )

            url: str = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(seconds=expires_seconds),
            )

            self._logger.debug(
                msg="Presigned URL generated successfully",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "expires_seconds": expires_seconds,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to generate presigned URL: {exc!s}",
                extra={
                    "bucket_name": bucket,
                    "object_name": object_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return url


minio_adapter: MinIOAdapter | None = None


async def get_minio_adapter() -> MinIOAdapter:
    """Get MinIO Adapter Instance.

    Arguments:
        None

    Returns:
        MinIOAdapter: MinIO adapter instance.

    Raises:
        RuntimeError: If MinIO is not enabled.
    """

    global minio_adapter  # noqa: PLW0603

    if not settings.minio_enabled:
        msg = "MinIO is not enabled in settings"
        raise RuntimeError(msg)

    if minio_adapter is None:
        minio_adapter = MinIOAdapter()

    return minio_adapter


async def initialize_minio() -> MinIOAdapter | None:
    """Initialize MinIO Connection.

    Arguments:
        None

    Returns:
        MinIOAdapter | None: MinIO adapter instance if enabled, None otherwise.

    Raises:
        None
    """

    if not settings.minio_enabled:
        logger: logging.Logger = get_logger(name="minio.initialize")
        logger.info(msg="MinIO is disabled")
        return None

    logger: logging.Logger = get_logger(name="minio.initialize")

    try:
        adapter: MinIOAdapter = await get_minio_adapter()
        await adapter.connect()

        is_healthy: bool = await adapter.health_check()
        if not is_healthy:
            logger.warning(msg="MinIO health check failed")
            return None

        await adapter.create_bucket()

        logger.info(msg="MinIO initialization successful")

    except Exception as exc:
        logger.warning(
            msg=f"Failed to initialize MinIO (service will continue without MinIO): {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    else:
        return adapter


async def shutdown_minio() -> None:
    """Shutdown MinIO Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global minio_adapter  # noqa: PLW0603

    if minio_adapter is not None:
        try:
            await minio_adapter.disconnect()
            minio_adapter = None

        except Exception as exc:
            logger: logging.Logger = get_logger(name="minio.shutdown")
            logger.warning(
                msg=f"Error during MinIO shutdown: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )


__all__: list[str] = [
    "MinIOAdapter",
    "get_minio_adapter",
    "initialize_minio",
    "shutdown_minio",
]
