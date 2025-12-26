import json
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import ValidationError

from config.logger import get_logger
from src.schemas import WebSocketErrorResponse
from src.schemas import WebSocketPingRequest
from src.schemas import WebSocketPongResponse

if TYPE_CHECKING:
    import logging


class PingWebSocketController:
    """Unprotected WebSocket Ping-Pong Controller.

    Inherits:
        object

    Attributes:
        _logger (logging.Logger): Logger instance for WebSocket operations.
        router (APIRouter): FastAPI router for WebSocket endpoints.

    Properties:
        None

    Methods:
        handle_ping_pong: Handle WebSocket ping-pong communication.
        _setup_routes: Setup FastAPI routes for WebSocket endpoints.
    """

    def __init__(self) -> None:
        """Initialize Ping WebSocket Controller.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="controller.websocket.ping")
        self.router: APIRouter = APIRouter(prefix="/websocket/ping", tags=["WebSocket - Unprotected"])
        self._setup_routes()

    async def handle_ping_pong(self, websocket: WebSocket) -> None:
        """Handle WebSocket Ping-Pong Communication.

        Arguments:
            websocket (WebSocket): WebSocket connection instance.

        Returns:
            None

        Raises:
            WebSocketDisconnect: When client disconnects.
        """

        await websocket.accept()

        client_host: str = websocket.client.host if websocket.client else "unknown"

        self._logger.info(
            msg="WebSocket connection established (unprotected)",
            extra={
                "client_host": client_host,
                "endpoint": "/api/v1/websocket/ping",
            },
        )

        try:
            while True:
                raw_message: str = await websocket.receive_text()

                self._logger.debug(
                    msg="Received WebSocket message",
                    extra={
                        "client_host": client_host,
                        "message_length": len(raw_message),
                    },
                )

                try:
                    message_data: dict = json.loads(raw_message)

                    ping_request: WebSocketPingRequest = WebSocketPingRequest(**message_data)

                    current_time: datetime = datetime.now(tz=UTC)

                    pong_response: WebSocketPongResponse = WebSocketPongResponse(
                        status="success",
                        message="Pong",
                        timestamp=current_time,
                        echo=ping_request.message,
                    )

                    await websocket.send_text(pong_response.model_dump_json())

                    self._logger.debug(
                        msg="Sent pong response",
                        extra={
                            "client_host": client_host,
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
                            "exception_type": type(exc).__name__,
                        },
                    )

        except WebSocketDisconnect:
            self._logger.info(
                msg="WebSocket connection closed",
                extra={
                    "client_host": client_host,
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
        async def websocket_ping_endpoint(websocket: WebSocket) -> None:
            """WebSocket Ping-Pong Endpoint (Unprotected).

            Arguments:
                websocket (WebSocket): WebSocket connection instance.

            Returns:
                None

            Raises:
                WebSocketDisconnect: When client disconnects.
            """

            await self.handle_ping_pong(websocket=websocket)


ping_websocket_controller: PingWebSocketController = PingWebSocketController()


__all__: list[str] = ["PingWebSocketController", "ping_websocket_controller"]
