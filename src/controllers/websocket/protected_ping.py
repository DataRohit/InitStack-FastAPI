# ruff: noqa: S105

import json
import uuid
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy import Result
from sqlalchemy import select

from config.adapters.postgresql import PostgreSQLAdapter
from config.adapters.postgresql import get_postgresql_adapter
from config.adapters.redis import TokenCacheRedisAdapter
from config.adapters.redis import get_token_cache_redis_adapter
from config.logger import get_logger
from src.models.users import User
from src.schemas import WebSocketErrorResponse
from src.schemas import WebSocketPingRequest
from src.schemas import WebSocketPongResponse
from src.utils.auth_tokens import validate_access_token

if TYPE_CHECKING:
    import logging

    from sqlalchemy.ext.asyncio import AsyncSession


class ProtectedPingWebSocketController:
    """Protected WebSocket Ping-Pong Controller With JWT Authentication.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for WebSocket operations.
        router (APIRouter): FastAPI router for WebSocket endpoints.

    Properties:
        None

    Methods:
        handle_ping_pong: Handle WebSocket ping-pong communication with authentication.
        _authenticate_websocket: Authenticate WebSocket connection using JWT token.
        _setup_routes: Setup FastAPI routes for WebSocket endpoints.
    """

    def __init__(self) -> None:
        """Initialize Protected Ping WebSocket Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.websocket.protected_ping")
        self.router: APIRouter = APIRouter(prefix="/websocket/protected-ping", tags=["WebSocket - Protected"])
        self._setup_routes()

    async def _authenticate_websocket(self, token: str) -> User | None:  # noqa: C901, PLR0911
        """Authenticate WebSocket Connection Using JWT Token.

        Arguments:
            token (str): JWT access token.

        Returns:
            User | None: Authenticated user or None if authentication fails.

        Raises:
            None
        """

        try:
            token_status: str
            payload: dict[str, object] | None
            token_status, payload = await validate_access_token(token=token)

            if token_status != "valid" or payload is None:
                self._logger.warning(
                    msg="Invalid access token",
                    extra={"token_status": token_status},
                )
                return None

            raw_user_id: object = payload.get("sub")
            if not isinstance(raw_user_id, str) or not raw_user_id:
                self._logger.warning(msg="Invalid user ID in token payload")
                return None

            try:
                user_uuid: uuid.UUID = uuid.UUID(hex=raw_user_id)
            except ValueError:
                self._logger.warning(msg="Invalid UUID format in token payload")
                return None

            user_id: str = str(object=user_uuid)

            try:
                token_cache_adapter: TokenCacheRedisAdapter = await get_token_cache_redis_adapter()
                if not token_cache_adapter.is_connected:
                    await token_cache_adapter.connect()

                access_key: str = f"access_token:{user_id}"
                cached_token: str | None = await token_cache_adapter.get(access_key)

                if cached_token is None or cached_token != token:
                    self._logger.warning(
                        msg="Token not found in cache or mismatch",
                        extra={"user_id": user_id},
                    )
                    return None
            except Exception as exc:
                self._logger.warning(
                    msg="Failed to verify token in cache",
                    extra={"error": str(object=exc)},
                )

            try:
                postgresql_adapter: PostgreSQLAdapter = await get_postgresql_adapter()
            except RuntimeError as exc:
                self._logger.exception(
                    msg="PostgreSQL adapter unavailable",
                    extra={"error": str(object=exc)},
                )
                return None

            session: AsyncSession = await postgresql_adapter.get_session()

            async with session as db:
                result: Result[tuple[User]] = await db.execute(statement=select(User).where(User.id == user_uuid))
                user: User | None = result.scalar_one_or_none()

            if user is None:
                self._logger.warning(
                    msg="User not found in database",
                    extra={"user_id": user_id},
                )
                return None

            if not user.is_active:
                self._logger.warning(
                    msg="User account is not active",
                    extra={"user_id": user_id},
                )
                return None

        except Exception as exc:
            self._logger.exception(
                msg="Unexpected error during authentication",
                extra={"exception_type": type(exc).__name__},
            )
            return None

        else:
            return user

    async def handle_ping_pong(self, websocket: WebSocket, token: str) -> None:
        """Handle WebSocket Ping-Pong Communication With Authentication.

        Arguments:
            websocket (WebSocket): WebSocket connection instance.
            token (str): JWT access token for authentication.

        Returns:
            None

        Raises:
            WebSocketDisconnect: When client disconnects.
        """

        user: User | None = await self._authenticate_websocket(token=token)

        if user is None:
            current_time: datetime = datetime.now(tz=UTC)
            error_response: WebSocketErrorResponse = WebSocketErrorResponse(
                status="error",
                message="Authentication Failed",
                timestamp=current_time,
                detail="Invalid or expired access token. Please provide a valid token.",
            )
            await websocket.accept()
            await websocket.send_text(error_response.model_dump_json())
            await websocket.close(code=1008, reason="Authentication failed")
            return

        await websocket.accept()

        client_host: str = websocket.client.host if websocket.client else "unknown"

        self._logger.info(
            msg="WebSocket connection established (protected)",
            extra={
                "client_host": client_host,
                "user_id": str(object=user.id),
                "user_email": user.email,
                "endpoint": "/api/v1/websocket/protected-ping",
            },
        )

        try:
            while True:
                raw_message: str = await websocket.receive_text()

                self._logger.debug(
                    msg="Received WebSocket message",
                    extra={
                        "client_host": client_host,
                        "user_id": str(object=user.id),
                        "message_length": len(raw_message),
                    },
                )

                try:
                    message_data: dict = json.loads(raw_message)

                    ping_request: WebSocketPingRequest = WebSocketPingRequest(**message_data)

                    current_time: datetime = datetime.now(tz=UTC)

                    pong_response: WebSocketPongResponse = WebSocketPongResponse(
                        status="success",
                        message=f"Pong (authenticated as {user.email})",
                        timestamp=current_time,
                        echo=ping_request.message,
                    )

                    await websocket.send_text(pong_response.model_dump_json())

                    self._logger.debug(
                        msg="Sent pong response",
                        extra={
                            "client_host": client_host,
                            "user_id": str(object=user.id),
                            "echo_message": ping_request.message,
                        },
                    )

                except json.JSONDecodeError as exc:
                    current_time: datetime = datetime.now(tz=UTC)

                    error_response: WebSocketErrorResponse = WebSocketErrorResponse(
                        status="error",
                        message="Invalid JSON Format",
                        timestamp=current_time,
                        detail=f"Failed to parse JSON: {exc!s}",
                    )

                    await websocket.send_text(error_response.model_dump_json())

                    self._logger.warning(
                        msg="Invalid JSON received",
                        extra={
                            "client_host": client_host,
                            "user_id": str(object=user.id),
                            "error": str(object=exc),
                        },
                    )

                except ValidationError as exc:
                    current_time: datetime = datetime.now(tz=UTC)

                    error_response: WebSocketErrorResponse = WebSocketErrorResponse(
                        status="error",
                        message="Validation Error",
                        timestamp=current_time,
                        detail=f"Message validation failed: {exc!s}",
                    )

                    await websocket.send_text(error_response.model_dump_json())

                    self._logger.warning(
                        msg="Message validation failed",
                        extra={
                            "client_host": client_host,
                            "user_id": str(object=user.id),
                            "validation_errors": exc.errors(),
                        },
                    )

                except Exception as exc:
                    current_time: datetime = datetime.now(tz=UTC)

                    error_response: WebSocketErrorResponse = WebSocketErrorResponse(
                        status="error",
                        message="Internal Server Error",
                        timestamp=current_time,
                        detail=f"An unexpected error occurred: {type(exc).__name__}",
                    )

                    await websocket.send_text(error_response.model_dump_json())

                    self._logger.exception(
                        msg="Unexpected error processing WebSocket message",
                        extra={
                            "client_host": client_host,
                            "user_id": str(object=user.id),
                            "exception_type": type(exc).__name__,
                        },
                    )

        except WebSocketDisconnect:
            self._logger.info(
                msg="WebSocket connection closed",
                extra={
                    "client_host": client_host,
                    "user_id": str(object=user.id),
                },
            )

    def _setup_routes(self) -> None:
        """Setup FastAPI Routes For WebSocket Endpoints.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        @self.router.websocket(path="")
        async def websocket_protected_ping_endpoint(websocket: WebSocket, token: str) -> None:
            """WebSocket Ping-Pong Endpoint (Protected With JWT).

            Arguments:
                websocket (WebSocket): WebSocket connection instance.
                token (str): JWT access token for authentication.

            Returns:
                None

            Raises:
                WebSocketDisconnect: When client disconnects.
            """

            await self.handle_ping_pong(websocket=websocket, token=token)


protected_ping_websocket_controller: ProtectedPingWebSocketController = ProtectedPingWebSocketController()


__all__: list[str] = ["ProtectedPingWebSocketController", "protected_ping_websocket_controller"]
