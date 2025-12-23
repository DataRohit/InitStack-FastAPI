from typing import TYPE_CHECKING
from typing import Any

from supabase import AsyncClient
from supabase import create_async_client

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging


class SupabaseAdapter:
    """Professional Production-Grade Supabase Database Adapter.

    Inherits:
        object

    Attributes:
        _client (AsyncClient): Async Supabase client instance.
        _logger (logging.Logger): Logger instance for Supabase operations.
        _is_connected (bool): Connection status flag.

    Properties:
        client: Get Supabase client instance.
        is_connected: Get connection status.
        connection_info: Get connection information.

    Methods:
        connect: Establish Supabase connection.
        disconnect: Close Supabase connection.
        health_check: Perform Supabase health check.
        select: Select data from table.
        insert: Insert data into table.
        update: Update data in table.
        delete: Delete data from table.
        upsert: Upsert data into table.
        rpc: Execute remote procedure call.
    """

    def __init__(self) -> None:
        """Initialize Supabase Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="supabase.adapter")

        self._client: AsyncClient | None = None

        self._is_connected: bool = False

        self._logger.info(
            msg="Supabase adapter initialized",
            extra={
                "supabase_url": settings.supabase_url,
                "supabase_schema": settings.supabase_schema,
                "connection_timeout": settings.supabase_connection_timeout,
                "request_timeout": settings.supabase_request_timeout,
            },
        )

    @property
    def client(self) -> AsyncClient:
        """Get Supabase Client Instance.

        Arguments:
            None

        Returns:
            AsyncClient: Supabase client instance.

        Raises:
            RuntimeError: If Supabase client is not connected.
        """

        if not self._client or not self._is_connected:
            msg = "Supabase client is not connected. Call connect() first."
            raise RuntimeError(msg)

        return self._client

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to Supabase, False otherwise.

        Raises:
            None
        """

        return self._is_connected

    @property
    def connection_info(self) -> dict[str, Any]:
        """Get Connection Information.

        Arguments:
            None

        Returns:
            dict[str, Any]: Connection information.

        Raises:
            None
        """

        info: dict[str, Any] = {
            "url": settings.supabase_url,
            "schema": settings.supabase_schema,
            "is_connected": self._is_connected,
            "connection_timeout": settings.supabase_connection_timeout,
            "request_timeout": settings.supabase_request_timeout,
        }

        return info

    async def connect(self) -> bool:
        """Establish Supabase Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="Supabase client is already connected")
                return True

            self._logger.info(msg="Establishing Supabase connection")

            self._client = await create_async_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_key,
            )

            self._is_connected = True

            self._logger.info(
                msg="Supabase connection established successfully",
                extra={
                    "supabase_url": settings.supabase_url,
                    "supabase_schema": settings.supabase_schema,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish Supabase connection: {exc!s}",
                extra={
                    "supabase_url": settings.supabase_url,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close Supabase Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="Supabase client is not connected")
                return

            self._logger.info(msg="Closing Supabase connection")

            if self._client:
                await self._client.auth.sign_out()
                self._client = None

            self._is_connected = False

            self._logger.info(msg="Supabase connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing Supabase connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform Supabase Health Check.

        Arguments:
            None

        Returns:
            bool: True if Supabase is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing Supabase health check")

            response = await self._client.table("_supabase_health").select("*").limit(1).execute()  # ty:ignore[possibly-missing-attribute]

            is_healthy: bool = response is not None

            self._logger.debug(
                msg=f"Supabase health check completed: {'healthy' if is_healthy else 'unhealthy'}",
                extra={"is_healthy": is_healthy},
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"Supabase health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return is_healthy

    async def select(  # noqa: PLR0913
        self,
        table: str,
        columns: str = "*",
        *,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> dict[str, Any]:
        """Select Data From Table.

        Arguments:
            table (str): Table name.
            columns (str): Columns to select (default: "*").
            filters (dict[str, Any] | None): Filter conditions.
            limit (int | None): Maximum number of rows to return.
            offset (int | None): Number of rows to skip.
            order_by (str | None): Column to order by.

        Returns:
            dict[str, Any]: Query response with data.

        Raises:
            Exception: If query fails.
        """

        try:
            self._logger.debug(
                msg="Selecting data from Supabase",
                extra={"table": table, "columns": columns, "filters": filters},
            )

            query = self.client.table(table).select(columns)

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            if order_by:
                query = query.order(order_by)

            response = await query.execute()

            self._logger.debug(
                msg="Data selected from Supabase",
                extra={"table": table, "row_count": len(response.data) if response.data else 0},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to select data from Supabase: {exc!s}",  # noqa: S608
                extra={"table": table, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return {"data": response.data, "count": response.count}

    async def insert(self, table: str, data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
        """Insert Data Into Table.

        Arguments:
            table (str): Table name.
            data (dict[str, Any] | list[dict[str, Any]]): Data to insert.

        Returns:
            dict[str, Any]: Insert response with data.

        Raises:
            Exception: If insert fails.
        """

        try:
            self._logger.debug(
                msg="Inserting data into Supabase",
                extra={"table": table, "is_bulk": isinstance(data, list)},
            )

            response = await self.client.table(table).insert(data).execute()

            self._logger.debug(
                msg="Data inserted into Supabase",
                extra={"table": table, "row_count": len(response.data) if response.data else 0},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to insert data into Supabase: {exc!s}",
                extra={"table": table, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return {"data": response.data, "count": response.count}

    async def update(self, table: str, data: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
        """Update Data In Table.

        Arguments:
            table (str): Table name.
            data (dict[str, Any]): Data to update.
            filters (dict[str, Any]): Filter conditions.

        Returns:
            dict[str, Any]: Update response with data.

        Raises:
            Exception: If update fails.
        """

        try:
            self._logger.debug(
                msg="Updating data in Supabase",
                extra={"table": table, "filters": filters},
            )

            query = self.client.table(table).update(data)

            for key, value in filters.items():
                query = query.eq(key, value)

            response = await query.execute()

            self._logger.debug(
                msg="Data updated in Supabase",
                extra={"table": table, "row_count": len(response.data) if response.data else 0},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to update data in Supabase: {exc!s}",
                extra={"table": table, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return {"data": response.data, "count": response.count}

    async def delete(self, table: str, filters: dict[str, Any]) -> dict[str, Any]:
        """Delete Data From Table.

        Arguments:
            table (str): Table name.
            filters (dict[str, Any]): Filter conditions.

        Returns:
            dict[str, Any]: Delete response with data.

        Raises:
            Exception: If delete fails.
        """

        try:
            self._logger.debug(
                msg="Deleting data from Supabase",
                extra={"table": table, "filters": filters},
            )

            query = self.client.table(table).delete()

            for key, value in filters.items():
                query = query.eq(key, value)

            response = await query.execute()

            self._logger.debug(
                msg="Data deleted from Supabase",
                extra={"table": table, "row_count": len(response.data) if response.data else 0},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete data from Supabase: {exc!s}",
                extra={"table": table, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return {"data": response.data, "count": response.count}

    async def upsert(self, table: str, data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
        """Upsert Data Into Table.

        Arguments:
            table (str): Table name.
            data (dict[str, Any] | list[dict[str, Any]]): Data to upsert.

        Returns:
            dict[str, Any]: Upsert response with data.

        Raises:
            Exception: If upsert fails.
        """

        try:
            self._logger.debug(
                msg="Upserting data into Supabase",
                extra={"table": table, "is_bulk": isinstance(data, list)},
            )

            response = await self.client.table(table).upsert(data).execute()

            self._logger.debug(
                msg="Data upserted into Supabase",
                extra={"table": table, "row_count": len(response.data) if response.data else 0},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to upsert data into Supabase: {exc!s}",
                extra={"table": table, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return {"data": response.data, "count": response.count}

    async def rpc(self, function: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Remote Procedure Call.

        Arguments:
            function (str): Function name.
            params (dict[str, Any] | None): Function parameters.

        Returns:
            dict[str, Any]: RPC response with data.

        Raises:
            Exception: If RPC fails.
        """

        try:
            self._logger.debug(
                msg="Executing RPC in Supabase",
                extra={"function": function, "params": params},
            )

            response = await self.client.rpc(function, params or {}).execute()

            self._logger.debug(
                msg="RPC executed in Supabase",
                extra={"function": function},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to execute RPC in Supabase: {exc!s}",
                extra={"function": function, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return {"data": response.data}


supabase_adapter: SupabaseAdapter | None = None


async def get_supabase_adapter() -> SupabaseAdapter:
    """Get Supabase Adapter Instance.

    Arguments:
        None

    Returns:
        SupabaseAdapter: Supabase adapter instance.

    Raises:
        RuntimeError: If Supabase is not enabled.
    """

    global supabase_adapter  # noqa: PLW0603

    if not settings.supabase_enabled:
        msg = "Supabase is not enabled in settings"
        raise RuntimeError(msg)

    if supabase_adapter is None:
        supabase_adapter = SupabaseAdapter()

    return supabase_adapter


async def initialize_supabase() -> SupabaseAdapter | None:
    """Initialize Supabase Connection.

    Arguments:
        None

    Returns:
        SupabaseAdapter | None: Supabase adapter instance if enabled, None otherwise.

    Raises:
        None
    """

    if not settings.supabase_enabled:
        logger: logging.Logger = get_logger(name="supabase.initialize")
        logger.info(msg="Supabase connection is disabled")
        return None

    logger: logging.Logger = get_logger(name="supabase.initialize")

    try:
        adapter: SupabaseAdapter = await get_supabase_adapter()

        await adapter.connect()

        logger.info(msg="Supabase connection successful")

    except Exception as exc:
        logger.warning(
            msg=f"Failed to initialize Supabase (service will continue without Supabase): {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    else:
        return adapter


async def shutdown_supabase() -> None:
    """Shutdown Supabase Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global supabase_adapter  # noqa: PLW0603

    if supabase_adapter is not None:
        try:
            await supabase_adapter.disconnect()

            supabase_adapter = None

        except Exception as exc:
            logger: logging.Logger = get_logger(name="supabase.shutdown")

            logger.warning(
                msg=f"Error during Supabase shutdown: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )


__all__: list[str] = [
    "SupabaseAdapter",
    "get_supabase_adapter",
    "initialize_supabase",
    "shutdown_supabase",
]
