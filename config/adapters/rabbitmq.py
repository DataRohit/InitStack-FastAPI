from typing import TYPE_CHECKING
from typing import Any
from urllib.parse import quote

from aio_pika import ExchangeType
from aio_pika import Message
from aio_pika import connect_robust

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging

    from aio_pika.abc import AbstractChannel
    from aio_pika.abc import AbstractConnection
    from aio_pika.abc import AbstractExchange
    from aio_pika.abc import AbstractQueue


class RabbitMQAdapter:
    """Professional Production-Grade RabbitMQ Message Broker Adapter.

    Inherits:
        object

    Attributes:
        _connection (AbstractConnection): Async RabbitMQ connection instance.
        _channel (AbstractChannel): RabbitMQ channel instance.
        _logger (logging.Logger): Logger instance for RabbitMQ operations.
        _is_connected (bool): Connection status flag.

    Properties:
        connection: Get RabbitMQ connection instance.
        channel: Get RabbitMQ channel instance.
        is_connected: Get connection status.

    Methods:
        connect: Establish RabbitMQ connection.
        disconnect: Close RabbitMQ connection.
        health_check: Perform RabbitMQ health check.
        declare_exchange: Declare exchange.
        declare_queue: Declare queue.
        bind_queue: Bind queue to exchange.
        publish_message: Publish message to exchange.
        consume_messages: Consume messages from queue.
        purge_queue: Purge queue.
        delete_queue: Delete queue.
        delete_exchange: Delete exchange.
        get_queue_info: Get queue information.
        get_connection_info: Get connection information.
        _build_connection_url: Build RabbitMQ connection URL.
    """

    def __init__(self) -> None:
        """Initialize RabbitMQ Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="rabbitmq.adapter")
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._is_connected: bool = False

        self._logger.info(
            msg="RabbitMQ adapter initialized",
            extra={
                "rabbitmq_host": settings.rabbitmq_host,
                "rabbitmq_port": settings.rabbitmq_port,
                "rabbitmq_vhost": settings.rabbitmq_vhost,
                "rabbitmq_ssl": settings.rabbitmq_ssl,
            },
        )

    @property
    def connection(self) -> AbstractConnection:
        """Get RabbitMQ Connection Instance.

        Arguments:
            None

        Returns:
            AbstractConnection: RabbitMQ connection instance.

        Raises:
            RuntimeError: If RabbitMQ connection is not established.
        """

        if not self._connection or not self._is_connected:
            msg = "RabbitMQ connection is not established. Call connect() first."
            raise RuntimeError(msg)

        return self._connection

    @property
    def channel(self) -> AbstractChannel:
        """Get RabbitMQ Channel Instance.

        Arguments:
            None

        Returns:
            AbstractChannel: RabbitMQ channel instance.

        Raises:
            RuntimeError: If RabbitMQ channel is not established.
        """

        if not self._channel or not self._is_connected:
            msg = "RabbitMQ channel is not established. Call connect() first."
            raise RuntimeError(msg)

        return self._channel

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to RabbitMQ, False otherwise.

        Raises:
            None
        """

        return self._is_connected

    async def connect(self) -> bool:
        """Establish RabbitMQ Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="RabbitMQ connection is already established")
                return True

            self._logger.info(msg="Establishing RabbitMQ connection")

            connection_url: str = self._build_connection_url()
            self._connection = await connect_robust(
                url=connection_url,
                timeout=settings.rabbitmq_connection_timeout,
            )

            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)

            self._is_connected = True

            self._logger.info(
                msg="RabbitMQ connection established successfully",
                extra={
                    "rabbitmq_host": settings.rabbitmq_host,
                    "rabbitmq_port": settings.rabbitmq_port,
                    "rabbitmq_vhost": settings.rabbitmq_vhost,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish RabbitMQ connection: {exc!s}",
                extra={
                    "rabbitmq_host": settings.rabbitmq_host,
                    "rabbitmq_port": settings.rabbitmq_port,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close RabbitMQ Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="RabbitMQ connection is not established")
                return

            self._logger.info(msg="Closing RabbitMQ connection")

            if self._channel:
                await self._channel.close()
                self._channel = None

            if self._connection:
                await self._connection.close()
                self._connection = None

            self._is_connected = False

            self._logger.info(msg="RabbitMQ connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing RabbitMQ connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform RabbitMQ Health Check.

        Arguments:
            None

        Returns:
            bool: True if RabbitMQ is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing RabbitMQ health check")

            is_healthy: bool = not self._connection.is_closed and not self._channel.is_closed  # ty:ignore[possibly-missing-attribute]

            self._logger.debug(
                msg=f"RabbitMQ health check completed: {'healthy' if is_healthy else 'unhealthy'}",
                extra={"is_healthy": is_healthy},
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"RabbitMQ health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return is_healthy

    async def declare_exchange(
        self,
        name: str,
        exchange_type: ExchangeType = ExchangeType.DIRECT,
        *,
        durable: bool = True,
        auto_delete: bool = False,
    ) -> AbstractExchange:
        """Declare Exchange.

        Arguments:
            name (str): Exchange name.
            exchange_type (ExchangeType): Exchange type.
            durable (bool): Whether exchange is durable.
            auto_delete (bool): Whether exchange auto-deletes.

        Returns:
            AbstractExchange: Declared exchange instance.

        Raises:
            Exception: If exchange declaration fails.
        """

        try:
            self._logger.debug(
                msg="Declaring exchange",
                extra={
                    "exchange_name": name,
                    "exchange_type": exchange_type.value,
                    "durable": durable,
                },
            )

            exchange: AbstractExchange = await self.channel.declare_exchange(
                name=name,
                type=exchange_type,
                durable=durable,
                auto_delete=auto_delete,
            )

            self._logger.debug(
                msg="Exchange declared successfully",
                extra={"exchange_name": name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to declare exchange: {exc!s}",
                extra={"exchange_name": name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return exchange

    async def declare_queue(
        self,
        name: str,
        *,
        durable: bool = True,
        auto_delete: bool = False,
        exclusive: bool = False,
    ) -> AbstractQueue:
        """Declare Queue.

        Arguments:
            name (str): Queue name.
            durable (bool): Whether queue is durable.
            auto_delete (bool): Whether queue auto-deletes.
            exclusive (bool): Whether queue is exclusive.

        Returns:
            AbstractQueue: Declared queue instance.

        Raises:
            Exception: If queue declaration fails.
        """

        try:
            self._logger.debug(
                msg="Declaring queue",
                extra={"queue_name": name, "durable": durable},
            )

            queue: AbstractQueue = await self.channel.declare_queue(
                name=name,
                durable=durable,
                auto_delete=auto_delete,
                exclusive=exclusive,
            )

            self._logger.debug(
                msg="Queue declared successfully",
                extra={"queue_name": name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to declare queue: {exc!s}",
                extra={"queue_name": name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return queue

    async def bind_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_key: str = "",
    ) -> None:
        """Bind Queue To Exchange.

        Arguments:
            queue_name (str): Queue name.
            exchange_name (str): Exchange name.
            routing_key (str): Routing key for binding.

        Returns:
            None

        Raises:
            Exception: If queue binding fails.
        """

        try:
            self._logger.debug(
                msg="Binding queue to exchange",
                extra={
                    "queue_name": queue_name,
                    "exchange_name": exchange_name,
                    "routing_key": routing_key,
                },
            )

            queue: AbstractQueue = await self.channel.get_queue(name=queue_name)
            await queue.bind(exchange=exchange_name, routing_key=routing_key)

            self._logger.debug(
                msg="Queue bound to exchange successfully",
                extra={"queue_name": queue_name, "exchange_name": exchange_name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to bind queue to exchange: {exc!s}",
                extra={
                    "queue_name": queue_name,
                    "exchange_name": exchange_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

    async def publish_message(
        self,
        exchange_name: str,
        routing_key: str,
        message_body: str | bytes,
        *,
        content_type: str = "text/plain",
        delivery_mode: int = 2,
    ) -> None:
        """Publish Message To Exchange.

        Arguments:
            exchange_name (str): Exchange name.
            routing_key (str): Routing key.
            message_body (str | bytes): Message body.
            content_type (str): Message content type.
            delivery_mode (int): Delivery mode (1=non-persistent, 2=persistent).

        Returns:
            None

        Raises:
            Exception: If message publishing fails.
        """

        try:
            self._logger.debug(
                msg="Publishing message to exchange",
                extra={
                    "exchange_name": exchange_name,
                    "routing_key": routing_key,
                    "content_type": content_type,
                },
            )

            if isinstance(message_body, str):
                message_body = message_body.encode()

            message: Message = Message(
                body=message_body,
                content_type=content_type,
                delivery_mode=delivery_mode,
            )

            exchange: AbstractExchange = await self.channel.get_exchange(name=exchange_name)
            await exchange.publish(message=message, routing_key=routing_key)

            self._logger.debug(
                msg="Message published successfully",
                extra={"exchange_name": exchange_name, "routing_key": routing_key},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to publish message: {exc!s}",
                extra={
                    "exchange_name": exchange_name,
                    "routing_key": routing_key,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

    async def purge_queue(self, queue_name: str) -> int:
        """Purge Queue.

        Arguments:
            queue_name (str): Queue name.

        Returns:
            int: Number of messages purged.

        Raises:
            Exception: If queue purging fails.
        """

        try:
            self._logger.debug(msg="Purging queue", extra={"queue_name": queue_name})

            queue: AbstractQueue = await self.channel.get_queue(name=queue_name)
            purged_result = await queue.purge()
            purged_count: int = int(purged_result.message_count) if purged_result.message_count is not None else 0

            self._logger.debug(
                msg="Queue purged successfully",
                extra={"queue_name": queue_name, "purged_count": purged_count},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to purge queue: {exc!s}",
                extra={"queue_name": queue_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return purged_count

    async def delete_queue(self, queue_name: str, *, if_unused: bool = False, if_empty: bool = False) -> None:
        """Delete Queue.

        Arguments:
            queue_name (str): Queue name.
            if_unused (bool): Delete only if unused.
            if_empty (bool): Delete only if empty.

        Returns:
            None

        Raises:
            Exception: If queue deletion fails.
        """

        try:
            self._logger.debug(msg="Deleting queue", extra={"queue_name": queue_name})

            queue: AbstractQueue = await self.channel.get_queue(name=queue_name)
            await queue.delete(if_unused=if_unused, if_empty=if_empty)

            self._logger.debug(
                msg="Queue deleted successfully",
                extra={"queue_name": queue_name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete queue: {exc!s}",
                extra={"queue_name": queue_name, "exception_type": type(exc).__name__},
            )
            raise

    async def delete_exchange(self, exchange_name: str, *, if_unused: bool = False) -> None:
        """Delete Exchange.

        Arguments:
            exchange_name (str): Exchange name.
            if_unused (bool): Delete only if unused.

        Returns:
            None

        Raises:
            Exception: If exchange deletion fails.
        """

        try:
            self._logger.debug(msg="Deleting exchange", extra={"exchange_name": exchange_name})

            exchange: AbstractExchange = await self.channel.get_exchange(name=exchange_name)
            await exchange.delete(if_unused=if_unused)

            self._logger.debug(
                msg="Exchange deleted successfully",
                extra={"exchange_name": exchange_name},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to delete exchange: {exc!s}",
                extra={"exchange_name": exchange_name, "exception_type": type(exc).__name__},
            )
            raise

    async def get_queue_info(self, queue_name: str) -> dict[str, Any]:
        """Get Queue Information.

        Arguments:
            queue_name (str): Queue name.

        Returns:
            dict[str, Any]: Queue information.

        Raises:
            Exception: If getting queue info fails.
        """

        try:
            self._logger.debug(msg="Getting queue information", extra={"queue_name": queue_name})

            queue: AbstractQueue = await self.channel.get_queue(name=queue_name)

            queue_info: dict[str, Any] = {
                "name": queue.name,
                "durable": queue.durable,
                "exclusive": queue.exclusive,
                "auto_delete": queue.auto_delete,
            }

            declaration_result = queue.declaration_result
            if declaration_result:
                queue_info["message_count"] = declaration_result.message_count
                queue_info["consumer_count"] = declaration_result.consumer_count

            self._logger.debug(
                msg="Queue information retrieved successfully",
                extra={"queue_name": queue_name, "queue_info": queue_info},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get queue information: {exc!s}",
                extra={"queue_name": queue_name, "exception_type": type(exc).__name__},
            )
            raise

        else:
            return queue_info

    async def get_connection_info(self) -> dict[str, Any]:
        """Get Connection Information.

        Arguments:
            None

        Returns:
            dict[str, Any]: Connection information.

        Raises:
            None
        """

        try:
            connection_info: dict[str, Any] = {
                "host": settings.rabbitmq_host,
                "port": settings.rabbitmq_port,
                "vhost": settings.rabbitmq_vhost,
                "ssl_enabled": settings.rabbitmq_ssl,
                "connection_name": settings.rabbitmq_connection_name,
                "is_connected": self._is_connected,
            }

            if self._connection and self._is_connected:
                connection_info["is_closed"] = self._connection.is_closed

            if self._channel and self._is_connected:
                connection_info["channel_is_closed"] = self._channel.is_closed
                connection_info["channel_number"] = self._channel.number

        except Exception as exc:
            self._logger.warning(
                msg=f"Error getting connection info: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return {"error": str(exc)}

        else:
            return connection_info

    def _build_connection_url(self) -> str:
        """Build RabbitMQ Connection URL.

        Arguments:
            None

        Returns:
            str: RabbitMQ connection URL.

        Raises:
            None
        """

        protocol: str = "amqps" if settings.rabbitmq_ssl else "amqp"
        vhost_encoded: str = quote(settings.rabbitmq_vhost, safe="")

        connection_url: str = (
            f"{protocol}://{settings.rabbitmq_username}:{settings.rabbitmq_password}"
            f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}/{vhost_encoded}"
            f"?heartbeat={settings.rabbitmq_heartbeat}"
            f"&blocked_connection_timeout={settings.rabbitmq_blocked_connection_timeout}"
            f"&connection_name={settings.rabbitmq_connection_name}"
        )

        return connection_url


_rabbitmq_adapter_instance: RabbitMQAdapter | None = None


async def get_rabbitmq_adapter() -> RabbitMQAdapter:
    """Get RabbitMQ Adapter Singleton Instance.

    Arguments:
        None

    Returns:
        RabbitMQAdapter: RabbitMQ adapter instance.

    Raises:
        RuntimeError: If RabbitMQ is not enabled.
    """

    global _rabbitmq_adapter_instance  # noqa: PLW0603

    if not settings.rabbitmq_enabled:
        msg = "RabbitMQ is not enabled in settings"
        raise RuntimeError(msg)

    if _rabbitmq_adapter_instance is None:
        _rabbitmq_adapter_instance = RabbitMQAdapter()

    return _rabbitmq_adapter_instance


async def initialize_rabbitmq() -> RabbitMQAdapter | None:
    """Initialize RabbitMQ Connection.

    Arguments:
        None

    Returns:
        RabbitMQAdapter | None: RabbitMQ adapter instance if successful, None otherwise.

    Raises:
        None
    """

    try:
        if not settings.rabbitmq_enabled:
            return None

        adapter: RabbitMQAdapter = await get_rabbitmq_adapter()
        await adapter.connect()

    except Exception:
        return None

    else:
        return adapter


async def shutdown_rabbitmq() -> None:
    """Shutdown RabbitMQ Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global _rabbitmq_adapter_instance  # noqa: PLW0603

    logger: logging.Logger = get_logger(name="rabbitmq.shutdown")

    try:
        if _rabbitmq_adapter_instance is not None:
            await _rabbitmq_adapter_instance.disconnect()
            _rabbitmq_adapter_instance = None

    except Exception as exc:
        logger.warning(
            msg=f"Error during RabbitMQ shutdown: {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )


__all__: list[str] = [
    "RabbitMQAdapter",
    "get_rabbitmq_adapter",
    "initialize_rabbitmq",
    "shutdown_rabbitmq",
]
