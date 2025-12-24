from typing import TYPE_CHECKING
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging
    from collections.abc import Sequence

    from sqlalchemy import Row
    from sqlalchemy.engine import Result
    from sqlalchemy.pool import Pool


postgresql_adapter: PostgreSQLAdapter | None = None


class PostgreSQLAdapter:
    """Professional Production-Grade PostgreSQL Database Adapter.

    Inherits:
        object

    Attributes:
        _engine (AsyncEngine): SQLAlchemy async engine instance.
        _session_factory (async_sessionmaker): Session factory for creating sessions.
        _logger (logging.Logger): Logger instance for PostgreSQL operations.
        _is_connected (bool): Connection status flag.

    Properties:
        engine: Get SQLAlchemy engine instance.
        session_factory: Get session factory.
        is_connected: Get connection status.
        pool_stats: Get connection pool statistics.

    Methods:
        connect: Establish PostgreSQL connection.
        disconnect: Close PostgreSQL connection.
        health_check: Perform PostgreSQL health check.
        get_session: Get async database session.
        execute_raw: Execute raw SQL query.
        execute_many: Execute multiple SQL statements.
        fetch_one: Fetch single row from query.
        fetch_all: Fetch all rows from query.
        _create_engine: Create SQLAlchemy async engine.
        _build_database_url: Build PostgreSQL connection URL.
    """

    def __init__(self) -> None:
        """Initialize PostgreSQL Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="postgresql.adapter")
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._is_connected: bool = False

        self._logger.info(
            msg="PostgreSQL adapter initialized",
            extra={
                "postgresql_host": settings.postgresql_host,
                "postgresql_port": settings.postgresql_port,
                "postgresql_database": settings.postgresql_database,
                "pool_size": settings.postgresql_pool_size,
                "max_overflow": settings.postgresql_max_overflow,
            },
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get SQLAlchemy Engine Instance.

        Arguments:
            None

        Returns:
            AsyncEngine: SQLAlchemy async engine instance.

        Raises:
            RuntimeError: If PostgreSQL engine is not connected.
        """

        if not self._engine or not self._is_connected:
            msg = "PostgreSQL engine is not connected. Call connect() first."
            raise RuntimeError(msg)

        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get Session Factory.

        Arguments:
            None

        Returns:
            async_sessionmaker[AsyncSession]: Session factory instance.

        Raises:
            RuntimeError: If PostgreSQL session factory is not initialized.
        """

        if not self._session_factory or not self._is_connected:
            msg = "PostgreSQL session factory is not initialized. Call connect() first."
            raise RuntimeError(msg)

        return self._session_factory

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to PostgreSQL, False otherwise.

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

        if not self._engine:
            return {"status": "not_initialized"}

        try:
            pool: Pool = self._engine.pool

            stats: dict[str, Any] = {
                "status": "initialized",
                "pool_size": getattr(pool, "size", lambda: "unknown")(),
                "checked_in_connections": getattr(pool, "checkedin", lambda: "unknown")(),
                "checked_out_connections": getattr(pool, "checkedout", lambda: "unknown")(),
                "overflow_connections": getattr(pool, "overflow", lambda: "unknown")(),
                "total_connections": getattr(pool, "size", lambda: 0)() + getattr(pool, "overflow", lambda: 0)(),
            }

        except Exception:
            return {"status": "error_getting_stats"}

        else:
            return stats

    async def connect(self) -> bool:
        """Establish PostgreSQL Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="PostgreSQL engine is already connected")
                return True

            self._logger.info(msg="Establishing PostgreSQL connection")

            self._engine: AsyncEngine = self._create_engine()

            self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            async with self._engine.begin() as conn:
                await conn.execute(statement=text("SELECT 1"))

            self._is_connected = True

            self._logger.info(
                msg="PostgreSQL connection established successfully",
                extra={
                    "postgresql_host": settings.postgresql_host,
                    "postgresql_port": settings.postgresql_port,
                    "postgresql_database": settings.postgresql_database,
                    "pool_stats": self.pool_stats,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish PostgreSQL connection: {exc!s}",
                extra={
                    "postgresql_host": settings.postgresql_host,
                    "postgresql_port": settings.postgresql_port,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close PostgreSQL Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="PostgreSQL engine is not connected")
                return

            self._logger.info(msg="Closing PostgreSQL connection")

            if self._engine:
                await self._engine.dispose()
                self._engine = None

            self._session_factory = None
            self._is_connected = False

            self._logger.info(msg="PostgreSQL connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing PostgreSQL connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform PostgreSQL Health Check.

        Arguments:
            None

        Returns:
            bool: True if PostgreSQL is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing PostgreSQL health check")

            async with self.engine.begin() as conn:
                result: Result = await conn.execute(statement=text("SELECT version()"))
                version_info: Any = result.scalar()

            is_healthy: bool = version_info is not None

            self._logger.debug(
                msg=f"PostgreSQL health check completed: {'healthy' if is_healthy else 'unhealthy'}",
                extra={
                    "postgresql_version": version_info,
                    "is_healthy": is_healthy,
                    "pool_stats": self.pool_stats,
                },
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"PostgreSQL health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return is_healthy

    async def get_session(self) -> AsyncSession:
        """Get Async Database Session.

        Arguments:
            None

        Returns:
            AsyncSession: SQLAlchemy async session instance.

        Raises:
            RuntimeError: If session factory is not initialized.
        """

        try:
            self._logger.debug(msg="Creating new database session")

            session: AsyncSession = self.session_factory()

            self._logger.debug(msg="Database session created successfully")

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to create database session: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            raise

        else:
            return session

    async def execute_raw(self, query: str, params: dict[str, Any] | None = None) -> Result:
        """Execute Raw SQL Query.

        Arguments:
            query (str): SQL query string.
            params (dict[str, Any] | None): Query parameters.

        Returns:
            Result: SQLAlchemy result object.

        Raises:
            Exception: If query execution fails.
        """

        try:
            self._logger.debug(
                msg="Executing raw SQL query",
                extra={"query": query, "has_params": params is not None},
            )

            async with self._engine.begin() as conn:  # ty:ignore[possibly-missing-attribute]
                result: Result = await conn.execute(statement=text(query), parameters=params or {})

            self._logger.debug(msg="Raw SQL query executed successfully")

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to execute raw SQL query: {exc!s}",
                extra={"query": query, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return result

    async def execute_many(self, queries: list[str]) -> list[Result]:
        """Execute Multiple SQL Statements.

        Arguments:
            queries (list[str]): List of SQL query strings.

        Returns:
            list[Result]: List of SQLAlchemy result objects.

        Raises:
            Exception: If query execution fails.
        """

        try:
            self._logger.debug(
                msg="Executing multiple SQL queries",
                extra={"query_count": len(queries)},
            )

            results: list[Result] = []

            async with self.engine.begin() as conn:
                for query in queries:
                    result: Result = await conn.execute(statement=text(query))
                    results.append(result)

            self._logger.debug(
                msg="Multiple SQL queries executed successfully",
                extra={"query_count": len(queries)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to execute multiple SQL queries: {exc!s}",
                extra={"query_count": len(queries), "exception_type": type(exc).__name__},
            )
            raise

        else:
            return results

    async def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Fetch Single Row From Query.

        Arguments:
            query (str): SQL query string.
            params (dict[str, Any] | None): Query parameters.

        Returns:
            dict[str, Any] | None: Single row as dictionary, None if no results.

        Raises:
            Exception: If query execution fails.
        """

        try:
            self._logger.debug(
                msg="Fetching single row from query",
                extra={"query": query, "has_params": params is not None},
            )

            async with self.engine.begin() as conn:
                result: Result = await conn.execute(statement=text(query), parameters=params or {})
                row: Row | None = result.fetchone()

            row_dict: dict[str, Any] | None = dict(row._mapping) if row else None  # noqa: SLF001

            self._logger.debug(
                msg="Single row fetched from query",
                extra={"has_result": row_dict is not None},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to fetch single row from query: {exc!s}",
                extra={"query": query, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return row_dict

    async def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch All Rows From Query.

        Arguments:
            query (str): SQL query string.
            params (dict[str, Any] | None): Query parameters.

        Returns:
            list[dict[str, Any]]: List of rows as dictionaries.

        Raises:
            Exception: If query execution fails.
        """

        try:
            self._logger.debug(
                msg="Fetching all rows from query",
                extra={"query": query, "has_params": params is not None},
            )

            async with self.engine.begin() as conn:
                result: Result = await conn.execute(statement=text(query), parameters=params or {})
                rows: Sequence[Row] = result.fetchall()

            rows_list: list[dict[str, Any]] = [dict(row._mapping) for row in rows]  # noqa: SLF001

            self._logger.debug(
                msg="All rows fetched from query",
                extra={"row_count": len(rows_list)},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to fetch all rows from query: {exc!s}",
                extra={"query": query, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return rows_list

    def _create_engine(self) -> AsyncEngine:
        """Create SQLAlchemy Async Engine.

        Arguments:
            None

        Returns:
            AsyncEngine: Configured SQLAlchemy async engine.

        Raises:
            None
        """

        database_url: str = self._build_database_url()

        engine: AsyncEngine = create_async_engine(
            url=database_url,
            echo=settings.postgresql_echo,
            echo_pool=settings.postgresql_echo_pool,
            pool_size=settings.postgresql_pool_size,
            max_overflow=settings.postgresql_max_overflow,
            pool_timeout=settings.postgresql_pool_timeout,
            pool_recycle=settings.postgresql_pool_recycle,
            pool_pre_ping=settings.postgresql_pool_pre_ping,
        )

        self._logger.debug(
            msg="SQLAlchemy async engine created",
            extra={
                "database_url": database_url.replace(settings.postgresql_password, "***"),
                "pool_size": settings.postgresql_pool_size,
                "max_overflow": settings.postgresql_max_overflow,
            },
        )

        return engine

    def _build_database_url(self) -> str:
        """Build PostgreSQL Connection URL.

        Arguments:
            None

        Returns:
            str: PostgreSQL connection URL.

        Raises:
            None
        """

        ssl_param: str = f"?sslmode={settings.postgresql_ssl_mode}" if settings.postgresql_ssl_mode else ""

        database_url: str = (
            f"postgresql+psycopg://{settings.postgresql_username}:{settings.postgresql_password}"
            f"@{settings.postgresql_host}:{settings.postgresql_port}/{settings.postgresql_database}{ssl_param}"
        )

        return database_url


async def get_postgresql_adapter() -> PostgreSQLAdapter:
    """Get PostgreSQL Adapter Instance.

    Arguments:
        None

    Returns:
        PostgreSQLAdapter: PostgreSQL adapter instance.

    Raises:
        RuntimeError: If PostgreSQL is not enabled.
    """

    global postgresql_adapter  # noqa: PLW0603

    if not settings.postgresql_enabled:
        msg = "PostgreSQL is not enabled in settings"
        raise RuntimeError(msg)

    if postgresql_adapter is None:
        postgresql_adapter = PostgreSQLAdapter()

    return postgresql_adapter


async def initialize_postgresql() -> PostgreSQLAdapter | None:
    """Initialize PostgreSQL Connection.

    Arguments:
        None

    Returns:
        PostgreSQLAdapter | None: PostgreSQL adapter instance if enabled, None otherwise.

    Raises:
        None
    """

    if not settings.postgresql_enabled:
        logger: logging.Logger = get_logger(name="postgresql.initialize")
        logger.info(msg="PostgreSQL is disabled")
        return None

    logger: logging.Logger = get_logger(name="postgresql.initialize")

    try:
        adapter: PostgreSQLAdapter = await get_postgresql_adapter()
        await adapter.connect()

        is_healthy: bool = await adapter.health_check()
        if not is_healthy:
            logger.warning(msg="PostgreSQL health check failed")
            return None

        logger.info(msg="PostgreSQL initialization successful")

    except Exception as exc:
        logger.warning(
            msg=f"Failed to initialize PostgreSQL (service will continue without PostgreSQL): {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    else:
        return adapter


async def shutdown_postgresql() -> None:
    """Shutdown PostgreSQL Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global postgresql_adapter  # noqa: PLW0603

    if postgresql_adapter is not None:
        try:
            await postgresql_adapter.disconnect()
            postgresql_adapter = None

        except Exception as exc:
            logger: logging.Logger = get_logger(name="postgresql.shutdown")
            logger.warning(
                msg=f"Error during PostgreSQL shutdown: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )


__all__: list[str] = [
    "PostgreSQLAdapter",
    "get_postgresql_adapter",
    "initialize_postgresql",
    "shutdown_postgresql",
]
