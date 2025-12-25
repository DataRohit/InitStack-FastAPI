# ruff: noqa: INP001

import asyncio
from logging.config import fileConfig
from typing import TYPE_CHECKING

from sqlalchemy import MetaData
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from config.settings import settings
from src.models.base import Base

if TYPE_CHECKING:
    from alembic.config import Config
    from sqlalchemy.engine import Connection

config: Config = context.config

if config.config_file_name is not None:
    fileConfig(fname=config.config_file_name)

target_metadata: MetaData = Base.metadata


def get_url() -> str:
    """Get Database URL From Settings.

    Arguments:
        None

    Returns:
        str: PostgreSQL connection URL.

    Raises:
        None
    """

    return (
        f"postgresql+psycopg://{settings.postgresql_username}:{settings.postgresql_password}"
        f"@{settings.postgresql_host}:{settings.postgresql_port}/{settings.postgresql_database}"
    )


def run_migrations_offline() -> None:
    """Run Migrations In Offline Mode.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    url: str = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute Migrations With Connection.

    Arguments:
        connection (Connection): SQLAlchemy connection.

    Returns:
        None

    Raises:
        None
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run Migrations In Online Mode With Async Engine.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    configuration: dict[str, str] = config.get_section(name=config.config_ini_section, default={})
    configuration["sqlalchemy.url"] = get_url()

    connectable: AsyncEngine = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(fn=do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run Migrations In Online Mode.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    asyncio.run(main=run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
