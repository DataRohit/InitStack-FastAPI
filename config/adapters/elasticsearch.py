from typing import TYPE_CHECKING
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch import NotFoundError

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from elastic_transport import ObjectApiResponse


class ElasticsearchAdapter:
    """Professional Production-Grade Elasticsearch Search Engine Adapter.

    Inherits:
        object

    Attributes:
        _client (AsyncElasticsearch): Async Elasticsearch client instance.
        _logger (logging.Logger): Logger instance for Elasticsearch operations.
        _is_connected (bool): Connection status flag.

    Properties:
        client: Get Elasticsearch client instance.
        is_connected: Get connection status.

    Methods:
        connect: Establish Elasticsearch connection.
        disconnect: Close Elasticsearch connection.
        health_check: Perform Elasticsearch health check.
        create_index: Create index.
        delete_index: Delete index.
        index_exists: Check if index exists.
        get_index_info: Get index information.
        index_document: Index document.
        get_document: Get document by ID.
        update_document: Update document.
        delete_document: Delete document.
        search: Search documents.
        count: Count documents.
        bulk_index: Bulk index documents.
        get_cluster_info: Get cluster information.
    """

    def __init__(self) -> None:
        """Initialize Elasticsearch Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="elasticsearch.adapter")
        self._client: AsyncElasticsearch | None = None
        self._is_connected: bool = False

        self._logger.info(
            msg="Elasticsearch adapter initialized",
            extra={
                "elasticsearch_hosts": settings.elasticsearch_hosts,
                "elasticsearch_ssl": settings.elasticsearch_ssl,
            },
        )

    @property
    def client(self) -> AsyncElasticsearch:
        """Get Elasticsearch Client Instance.

        Arguments:
            None

        Returns:
            AsyncElasticsearch: Elasticsearch client instance.

        Raises:
            RuntimeError: If Elasticsearch client is not connected.
        """

        if not self._client or not self._is_connected:
            msg = "Elasticsearch client is not connected. Call connect() first."
            raise RuntimeError(msg)

        return self._client

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to Elasticsearch, False otherwise.

        Raises:
            None
        """

        return self._is_connected

    async def connect(self) -> bool:
        """Establish Elasticsearch Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="Elasticsearch connection is already established")
                return True

            self._logger.info(msg="Establishing Elasticsearch connection")

            self._client = AsyncElasticsearch(
                hosts=settings.elasticsearch_hosts,
                basic_auth=(settings.elasticsearch_username, settings.elasticsearch_password),
                verify_certs=settings.elasticsearch_ssl_verify,
                request_timeout=settings.elasticsearch_request_timeout,
                max_retries=settings.elasticsearch_max_retries,
                retry_on_timeout=settings.elasticsearch_retry_on_timeout,
            )

            await self._client.info()

            self._is_connected = True

            self._logger.info(
                msg="Elasticsearch connection established successfully",
                extra={"elasticsearch_hosts": settings.elasticsearch_hosts},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish Elasticsearch connection: {exc!s}",
                extra={
                    "elasticsearch_hosts": settings.elasticsearch_hosts,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close Elasticsearch Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="Elasticsearch connection is not established")
                return

            self._logger.info(msg="Closing Elasticsearch connection")

            if self._client:
                await self._client.close()
                self._client = None

            self._is_connected = False

            self._logger.info(msg="Elasticsearch connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing Elasticsearch connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform Elasticsearch Health Check.

        Arguments:
            None

        Returns:
            bool: True if Elasticsearch is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing Elasticsearch health check")

            await self.client.cluster.health()

            self._logger.debug(msg="Elasticsearch health check completed: healthy")

        except Exception as exc:
            self._logger.warning(
                msg=f"Elasticsearch health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return True

    async def create_index(self, index_name: str, *, mappings: dict[str, Any] | None = None) -> bool:
        """Create Index.

        Arguments:
            index_name (str): Index name.
            mappings (dict[str, Any] | None): Index mappings.

        Returns:
            bool: True if index created successfully.

        Raises:
            Exception: If index creation fails.
        """

        try:
            self._logger.debug(msg="Creating index", extra={"index_name": index_name})

            body: dict[str, Any] = {}
            if mappings:
                body["mappings"] = mappings

            await self.client.indices.create(index=index_name, body=body if body else None)

            self._logger.debug(msg="Index created successfully", extra={"index_name": index_name})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to create index: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return True

    async def delete_index(self, index_name: str) -> bool:
        """Delete Index.

        Arguments:
            index_name (str): Index name.

        Returns:
            bool: True if index deleted successfully.

        Raises:
            Exception: If index deletion fails.
        """

        try:
            self._logger.debug(msg="Deleting index", extra={"index_name": index_name})

            await self.client.indices.delete(index=index_name)

            self._logger.debug(msg="Index deleted successfully", extra={"index_name": index_name})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete index: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return True

    async def index_exists(self, index_name: str) -> bool:
        """Check If Index Exists.

        Arguments:
            index_name (str): Index name.

        Returns:
            bool: True if index exists, False otherwise.

        Raises:
            Exception: If check fails.
        """

        try:
            self._logger.debug(msg="Checking if index exists", extra={"index_name": index_name})

            exists: bool = await self.client.indices.exists(index=index_name)

            self._logger.debug(msg=f"Index exists: {exists}", extra={"index_name": index_name, "exists": exists})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to check if index exists: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return exists

    async def get_index_info(self, index_name: str) -> dict[str, Any]:
        """Get Index Information.

        Arguments:
            index_name (str): Index name.

        Returns:
            dict[str, Any]: Index information.

        Raises:
            Exception: If getting index info fails.
        """

        try:
            self._logger.debug(msg="Getting index information", extra={"index_name": index_name})

            index_info: dict[str, Any] = await self.client.indices.get(index=index_name)

            self._logger.debug(msg="Index information retrieved successfully", extra={"index_name": index_name})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get index information: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return index_info

    async def index_document(self, index_name: str, document: dict[str, Any], *, document_id: str | None = None) -> str:
        """Index Document.

        Arguments:
            index_name (str): Index name.
            document (dict[str, Any]): Document to index.
            document_id (str | None): Document ID.

        Returns:
            str: Document ID.

        Raises:
            Exception: If document indexing fails.
        """

        try:
            self._logger.debug(msg="Indexing document", extra={"index_name": index_name, "document_id": document_id})

            response: ObjectApiResponse = await self.client.index(index=index_name, id=document_id, document=document)

            doc_id: str = response["_id"]

            self._logger.debug(
                msg="Document indexed successfully",
                extra={"index_name": index_name, "document_id": doc_id},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to index document: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return doc_id

    async def get_document(self, index_name: str, document_id: str) -> dict[str, Any] | None:
        """Get Document By ID.

        Arguments:
            index_name (str): Index name.
            document_id (str): Document ID.

        Returns:
            dict[str, Any] | None: Document if found, None otherwise.

        Raises:
            Exception: If getting document fails.
        """

        try:
            self._logger.debug(
                msg="Getting document",
                extra={"index_name": index_name, "document_id": document_id},
            )

            response: ObjectApiResponse = await self.client.get(index=index_name, id=document_id)

            document: dict[str, Any] = response["_source"]

            self._logger.debug(
                msg="Document retrieved successfully",
                extra={"index_name": index_name, "document_id": document_id},
            )

        except NotFoundError:
            self._logger.debug(
                msg="Document not found",
                extra={"index_name": index_name, "document_id": document_id},
            )
            return None

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get document: {exc!s}",
                extra={
                    "index_name": index_name,
                    "document_id": document_id,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return document

    async def update_document(self, index_name: str, document_id: str, document: dict[str, Any]) -> bool:
        """Update Document.

        Arguments:
            index_name (str): Index name.
            document_id (str): Document ID.
            document (dict[str, Any]): Document updates.

        Returns:
            bool: True if document updated successfully.

        Raises:
            Exception: If document update fails.
        """

        try:
            self._logger.debug(
                msg="Updating document",
                extra={"index_name": index_name, "document_id": document_id},
            )

            await self.client.update(index=index_name, id=document_id, doc=document)

            self._logger.debug(
                msg="Document updated successfully",
                extra={"index_name": index_name, "document_id": document_id},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to update document: {exc!s}",
                extra={
                    "index_name": index_name,
                    "document_id": document_id,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def delete_document(self, index_name: str, document_id: str) -> bool:
        """Delete Document.

        Arguments:
            index_name (str): Index name.
            document_id (str): Document ID.

        Returns:
            bool: True if document deleted successfully.

        Raises:
            Exception: If document deletion fails.
        """

        try:
            self._logger.debug(
                msg="Deleting document",
                extra={"index_name": index_name, "document_id": document_id},
            )

            await self.client.delete(index=index_name, id=document_id)

            self._logger.debug(
                msg="Document deleted successfully",
                extra={"index_name": index_name, "document_id": document_id},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete document: {exc!s}",
                extra={
                    "index_name": index_name,
                    "document_id": document_id,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def search(self, index_name: str, query: dict[str, Any], *, size: int = 10) -> dict[str, Any]:
        """Search Documents.

        Arguments:
            index_name (str): Index name.
            query (dict[str, Any]): Search query.
            size (int): Number of results to return.

        Returns:
            dict[str, Any]: Search results.

        Raises:
            Exception: If search fails.
        """

        try:
            self._logger.debug(msg="Searching documents", extra={"index_name": index_name, "size": size})

            response: ObjectApiResponse = await self.client.search(index=index_name, query=query, size=size)

            self._logger.debug(
                msg="Search completed successfully",
                extra={"index_name": index_name, "hits": response["hits"]["total"]["value"]},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to search documents: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return response

    async def count(self, index_name: str, query: dict[str, Any] | None = None) -> int:
        """Count Documents.

        Arguments:
            index_name (str): Index name.
            query (dict[str, Any] | None): Count query.

        Returns:
            int: Document count.

        Raises:
            Exception: If count fails.
        """

        try:
            self._logger.debug(msg="Counting documents", extra={"index_name": index_name})

            response: ObjectApiResponse = await self.client.count(index=index_name, query=query)

            count: int = response["count"]

            self._logger.debug(msg="Count completed successfully", extra={"index_name": index_name, "count": count})

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to count documents: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return count

    async def bulk_index(self, index_name: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Bulk Index Documents.

        Arguments:
            index_name (str): Index name.
            documents (list[dict[str, Any]]): Documents to index.

        Returns:
            dict[str, Any]: Bulk operation results.

        Raises:
            Exception: If bulk indexing fails.
        """

        try:
            self._logger.debug(
                msg="Bulk indexing documents",
                extra={"index_name": index_name, "document_count": len(documents)},
            )

            operations: list[dict[str, Any]] = []
            for doc in documents:
                operations.append({"index": {"_index": index_name}})
                operations.append(doc)

            response: ObjectApiResponse = await self.client.bulk(operations=operations)

            self._logger.debug(
                msg="Bulk indexing completed successfully",
                extra={"index_name": index_name, "document_count": len(documents)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to bulk index documents: {exc!s}",
                extra={"index_name": index_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return response

    async def get_cluster_info(self) -> dict[str, Any]:
        """Get Cluster Information.

        Arguments:
            None

        Returns:
            dict[str, Any]: Cluster information.

        Raises:
            None
        """

        try:
            cluster_info: dict[str, Any] = {}

            info: ObjectApiResponse = await self.client.info()
            cluster_info["name"] = info.get("cluster_name")
            cluster_info["version"] = info.get("version", {}).get("number")

            health: ObjectApiResponse = await self.client.cluster.health()
            cluster_info["status"] = health.get("status")
            cluster_info["number_of_nodes"] = health.get("number_of_nodes")
            cluster_info["active_shards"] = health.get("active_shards")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error getting cluster info: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return {"error": str(object=exc)}

        else:
            return cluster_info


_elasticsearch_adapter_instance: ElasticsearchAdapter | None = None


async def get_elasticsearch_adapter() -> ElasticsearchAdapter:
    """Get Elasticsearch Adapter Singleton Instance.

    Arguments:
        None

    Returns:
        ElasticsearchAdapter: Elasticsearch adapter instance.

    Raises:
        RuntimeError: If Elasticsearch is not enabled.
    """

    global _elasticsearch_adapter_instance  # noqa: PLW0603

    if not settings.elasticsearch_enabled:
        msg = "Elasticsearch is not enabled in settings"
        raise RuntimeError(msg)

    if _elasticsearch_adapter_instance is None:
        _elasticsearch_adapter_instance = ElasticsearchAdapter()

    return _elasticsearch_adapter_instance


async def initialize_elasticsearch() -> ElasticsearchAdapter | None:
    """Initialize Elasticsearch Connection.

    Arguments:
        None

    Returns:
        ElasticsearchAdapter | None: Elasticsearch adapter instance if successful, None otherwise.

    Raises:
        None
    """

    try:
        if not settings.elasticsearch_enabled:
            return None

        adapter: ElasticsearchAdapter = await get_elasticsearch_adapter()
        await adapter.connect()

    except Exception:
        return None

    else:
        return adapter


async def shutdown_elasticsearch() -> None:
    """Shutdown Elasticsearch Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global _elasticsearch_adapter_instance  # noqa: PLW0603

    logger: logging.Logger = get_logger(name="elasticsearch.shutdown")

    try:
        if _elasticsearch_adapter_instance is not None:
            await _elasticsearch_adapter_instance.disconnect()
            _elasticsearch_adapter_instance = None

    except Exception as exc:
        logger.warning(
            msg=f"Error during Elasticsearch shutdown: {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )


__all__: list[str] = [
    "ElasticsearchAdapter",
    "get_elasticsearch_adapter",
    "initialize_elasticsearch",
    "shutdown_elasticsearch",
]
