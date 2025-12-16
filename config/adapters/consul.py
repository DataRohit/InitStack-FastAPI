import socket
import uuid
from typing import TYPE_CHECKING
from typing import Any

from consul.aio import Consul as AsyncConsul

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging


class ConsulAdapter:
    """Professional Production-Grade Consul Service Discovery Adapter.

    Inherits:
        object

    Attributes:
        _client (AsyncConsul): Async Consul client instance.
        _logger (logging.Logger): Logger instance for Consul operations.
        _service_id (str): Unique service identifier.
        _service_name (str): Service name for registration.
        _service_address (str): Service IP address.
        _service_port (int): Service port number.
        _health_check_url (str): Health check endpoint URL.
        _is_registered (bool): Service registration status.

    Properties:
        service_id: Get the service ID.
        service_name: Get the service name.
        is_registered: Get registration status.

    Methods:
        register_service: Register service with Consul.
        deregister_service: Deregister service from Consul.
        health_check: Perform health check against Consul.
        get_service_health: Get service health status from Consul.
        discover_services: Discover services by name.
        get_service_instances: Get all instances of a service.
        close: Close Consul client connection.
        _get_local_ip: Get local IP address for service registration.
        _generate_service_id: Generate unique service identifier.
        _build_health_check_config: Build health check configuration.
    """

    def __init__(self) -> None:
        """Initialize Consul Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="consul.adapter")
        self._service_address: str = self._get_local_ip()
        self._service_port: int = settings.port
        self._service_name: str = settings.consul_service_name
        self._service_id: str = self._generate_service_id()
        self._health_check_url: str = f"http://{self._service_address}:{self._service_port}/api/v1/health/"
        self._is_registered: bool = False

        self._client: AsyncConsul = AsyncConsul(
            host=settings.consul_host,
            port=settings.consul_port,
            token=settings.consul_token,
            scheme=settings.consul_scheme,
            dc=settings.consul_datacenter,
            verify=settings.consul_verify,
        )

        self._logger.info(
            msg="Consul adapter initialized",
            extra={
                "service_id": self._service_id,
                "service_name": self._service_name,
                "service_address": self._service_address,
                "service_port": self._service_port,
                "consul_host": settings.consul_host,
                "consul_port": settings.consul_port,
                "consul_datacenter": settings.consul_datacenter,
            },
        )

    @property
    def service_id(self) -> str:
        """Get The Service ID.

        Arguments:
            None

        Returns:
            str: Unique service identifier.

        Raises:
            None
        """

        return self._service_id

    @property
    def service_name(self) -> str:
        """Get The Service Name.

        Arguments:
            None

        Returns:
            str: Service name.

        Raises:
            None
        """

        return self._service_name

    @property
    def is_registered(self) -> bool:
        """Get Registration Status.

        Arguments:
            None

        Returns:
            bool: True if service is registered with Consul.

        Raises:
            None
        """

        return self._is_registered

    async def register_service(self) -> bool:
        """Register Service With Consul.

        Arguments:
            None

        Returns:
            bool: True if registration successful, False otherwise.

        Raises:
            Exception: If registration fails.
        """

        try:
            self._logger.info(
                msg="Registering service with Consul",
                extra={
                    "service_id": self._service_id,
                    "service_name": self._service_name,
                    "service_address": self._service_address,
                    "service_port": self._service_port,
                },
            )

            health_check_config: dict[str, Any] = self._build_health_check_config()

            await self._client.agent.service.register(
                name=self._service_name,
                service_id=self._service_id,
                address=self._service_address,
                port=self._service_port,
                tags=settings.consul_service_tags,
                meta={
                    "version": settings.app_version,
                    "environment": settings.environment,
                    "debug": str(settings.debug).lower(),
                    "description": settings.app_description,
                },
                check=health_check_config,
            )

            self._is_registered = True

            self._logger.info(
                msg="Service successfully registered with Consul",
                extra={
                    "service_id": self._service_id,
                    "service_name": self._service_name,
                    "health_check_url": self._health_check_url,
                    "tags": settings.consul_service_tags,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to register service with Consul: {exc!s}",
                extra={
                    "service_id": self._service_id,
                    "service_name": self._service_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def deregister_service(self) -> bool:
        """Deregister Service From Consul.

        Arguments:
            None

        Returns:
            bool: True if deregistration successful, False otherwise.

        Raises:
            Exception: If deregistration fails.
        """

        try:
            if not self._is_registered:
                self._logger.warning(
                    msg="Service is not registered, skipping deregistration",
                    extra={"service_id": self._service_id},
                )
                return True

            self._logger.info(
                msg="Deregistering service from Consul",
                extra={"service_id": self._service_id},
            )

            await self._client.agent.service.deregister(service_id=self._service_id)

            self._is_registered = False

            self._logger.info(
                msg="Service successfully deregistered from Consul",
                extra={"service_id": self._service_id},
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to deregister service from Consul: {exc!s}",
                extra={
                    "service_id": self._service_id,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def health_check(self) -> bool:
        """Perform Health Check Against Consul.

        Arguments:
            None

        Returns:
            bool: True if Consul is healthy, False otherwise.

        Raises:
            None
        """

        try:
            self._logger.debug(msg="Performing Consul health check")

            leader: str | None = await self._client.status.leader()
            peers: list[str] | None = await self._client.status.peers()

            is_healthy: bool = bool(leader and peers)

            self._logger.debug(
                msg=f"Consul health check completed: {'healthy' if is_healthy else 'unhealthy'}",
                extra={
                    "leader": leader,
                    "peers_count": len(peers) if peers else 0,
                    "is_healthy": is_healthy,
                },
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"Consul health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return is_healthy

    async def get_service_health(self, service_name: str | None = None) -> dict[str, Any]:
        """Get Service Health Status From Consul.

        Arguments:
            service_name (str | None): Service name to check (default: current service).

        Returns:
            dict[str, Any]: Service health information.

        Raises:
            Exception: If health check retrieval fails.
        """

        target_service: str = service_name or self._service_name

        try:
            self._logger.debug(
                msg="Retrieving service health from Consul",
                extra={"service_name": target_service},
            )

            health_data: list[Any] | None = None
            _, health_data = await self._client.health.service(service=target_service, passing=None)

            health_info: dict[str, Any] = {
                "service_name": target_service,
                "instances_count": len(health_data),
                "healthy_instances": len(
                    [h for h in health_data if all(check["Status"] == "passing" for check in h.get("Checks", []))],
                ),
                "instances": [],
            }

            for instance in health_data:
                service_info: dict[str, Any] | None = instance.get("Service", {})
                checks: list | None = instance.get("Checks", [])

                instance_info: dict[str, Any] = {
                    "service_id": service_info.get("ID"),
                    "address": service_info.get("Address"),
                    "port": service_info.get("Port"),
                    "tags": service_info.get("Tags", []),
                    "meta": service_info.get("Meta", {}),
                    "health_status": "passing" if all(check["Status"] == "passing" for check in checks) else "failing",
                    "checks": [
                        {
                            "name": check.get("Name"),
                            "status": check.get("Status"),
                            "output": check.get("Output", "").strip(),
                        }
                        for check in checks
                    ],
                }

                health_info["instances"].append(instance_info)

            self._logger.debug(
                msg="Service health retrieved successfully",
                extra={
                    "service_name": target_service,
                    "instances_count": health_info["instances_count"],
                    "healthy_instances": health_info["healthy_instances"],
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to retrieve service health from Consul: {exc!s}",
                extra={
                    "service_name": target_service,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return health_info

    async def discover_services(self, service_name: str, *, passing_only: bool = True) -> list[dict[str, Any]]:
        """Discover Services By Name.

        Arguments:
            service_name (str): Name of the service to discover.
            passing_only (bool): Return only healthy instances (default: True).

        Returns:
            list[dict[str, Any]]: List of service instances.

        Raises:
            Exception: If service discovery fails.
        """

        try:
            self._logger.debug(
                msg="Discovering services from Consul",
                extra={"service_name": service_name, "passing_only": passing_only},
            )

            services: list[dict[str, Any]] | None = None
            _, services = await self._client.health.service(service=service_name, passing=passing_only)

            discovered_services: list[dict[str, Any]] = []

            for service in services:
                service_info: dict[str, Any] = service.get("Service", {})

                service_data: dict[str, Any] = {
                    "service_id": service_info.get("ID"),
                    "service_name": service_info.get("Service"),
                    "address": service_info.get("Address"),
                    "port": service_info.get("Port"),
                    "tags": service_info.get("Tags", []),
                    "meta": service_info.get("Meta", {}),
                }

                discovered_services.append(service_data)

            self._logger.debug(
                msg="Service discovery completed",
                extra={
                    "service_name": service_name,
                    "instances_found": len(discovered_services),
                    "passing_only": passing_only,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to discover services from Consul: {exc!s}",
                extra={
                    "service_name": service_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return discovered_services

    async def get_service_instances(self, service_name: str) -> list[str]:
        """Get All Instances Of A Service.

        Arguments:
            service_name (str): Name of the service.

        Returns:
            list[str]: List of service instance URLs.

        Raises:
            Exception: If instance retrieval fails.
        """

        try:
            services: list[dict[str, Any]] = await self.discover_services(service_name=service_name, passing_only=True)

            instances: list[str] = [
                f"http://{service['address']}:{service['port']}"
                for service in services
                if service.get("address") and service.get("port")
            ]

            self._logger.debug(
                msg="Service instances retrieved",
                extra={
                    "service_name": service_name,
                    "instances_count": len(instances),
                    "instances": instances,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to get service instances: {exc!s}",
                extra={
                    "service_name": service_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return instances

    async def close(self) -> None:
        """Close Consul Client Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if self._is_registered:
                await self.deregister_service()

            if hasattr(self._client, "close"):
                await self._client.close()

            self._logger.info(msg="Consul client connection closed")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing Consul client: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    def _get_local_ip(self) -> str:
        """Get Local IP Address For Service Registration.

        Arguments:
            None

        Returns:
            str: Local IP address.

        Raises:
            None
        """

        try:
            with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                local_ip: str = sock.getsockname()[0]

            self._logger.debug(
                msg="Local IP address detected",
                extra={"local_ip": local_ip},
            )

        except Exception as exc:
            self._logger.warning(
                msg=f"Failed to detect local IP, using fallback: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return "127.0.0.1"

        else:
            return local_ip

    def _generate_service_id(self) -> str:
        """Generate Unique Service Identifier.

        Arguments:
            None

        Returns:
            str: Unique service ID.

        Raises:
            None
        """

        unique_id: str = str(object=uuid.uuid4())[:8]
        service_id: str = f"{self._service_name}-{self._service_address}-{self._service_port}-{unique_id}"

        self._logger.debug(
            msg="Service ID generated",
            extra={"service_id": service_id},
        )

        return service_id

    def _build_health_check_config(self) -> dict[str, Any]:
        """Build Health Check Configuration.

        Arguments:
            None

        Returns:
            dict[str, Any]: Health check configuration.

        Raises:
            None
        """

        health_check_config: dict[str, Any] = {
            "http": self._health_check_url,
            "interval": settings.consul_health_check_interval,
            "timeout": settings.consul_health_check_timeout,
            "deregister_critical_service_after": settings.consul_health_check_deregister_critical_after,
        }

        self._logger.debug(
            msg="Health check configuration built",
            extra={"health_check_config": health_check_config},
        )

        return health_check_config


consul_adapter: ConsulAdapter | None = None


async def get_consul_adapter() -> ConsulAdapter:
    """Get Consul Adapter Instance.

    Arguments:
        None

    Returns:
        ConsulAdapter: Consul adapter instance.

    Raises:
        RuntimeError: If Consul is not enabled.
    """

    global consul_adapter  # noqa: PLW0603

    if not settings.consul_enabled:
        msg = "Consul is not enabled in settings"
        raise RuntimeError(msg)

    if consul_adapter is None:
        consul_adapter = ConsulAdapter()

    return consul_adapter


async def initialize_consul() -> ConsulAdapter | None:
    """Initialize Consul Service Registration.

    Arguments:
        None

    Returns:
        ConsulAdapter | None: Consul adapter instance if enabled, None otherwise.

    Raises:
        None
    """

    if not settings.consul_enabled:
        logger: logging.Logger = get_logger(name="consul.initialize")
        logger.info(msg="Consul service discovery is disabled")
        return None

    logger: logging.Logger = get_logger(name="consul.initialize")

    try:
        adapter: ConsulAdapter = await get_consul_adapter()

        is_healthy = await adapter.health_check()
        if not is_healthy:
            logger.warning(msg="Consul health check failed, skipping service registration")
            return None

        await adapter.register_service()
        logger.info(msg="Consul service registration successful")

    except Exception as exc:
        logger.warning(
            msg=f"Failed to initialize Consul (service will continue without Consul): {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    else:
        return adapter


async def shutdown_consul() -> None:
    """Shutdown Consul Service Registration.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global consul_adapter  # noqa: PLW0603

    if consul_adapter is not None:
        try:
            await consul_adapter.close()
            consul_adapter = None

        except Exception as exc:
            logger: logging.Logger = get_logger(name="consul.shutdown")
            logger.warning(
                msg=f"Error during Consul shutdown: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )


__all__: list[str] = [
    "ConsulAdapter",
    "get_consul_adapter",
    "initialize_consul",
    "shutdown_consul",
]
