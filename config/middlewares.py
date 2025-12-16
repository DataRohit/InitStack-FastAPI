from typing import TYPE_CHECKING

from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware To Limit Request Body Size And Upload Size.

    Inherits:
        BaseHTTPMiddleware

    Attributes:
        max_request_size (int): Maximum request body size in bytes.
        max_upload_size (int): Maximum upload file size in bytes.

    Properties:
        None

    Methods:
        dispatch: Process request and check size limits.
    """

    def __init__(self, app, max_request_size: int = 16777216, max_upload_size: int = 104857600):
        """Initialize Request Size Limit Middleware.

        Arguments:
            app: ASGI application.
            max_request_size (int): Maximum request body size in bytes (default: 16MB).
            max_upload_size (int): Maximum upload file size in bytes (default: 100MB).

        Returns:
            None

        Raises:
            None
        """

        super().__init__(app)
        self.max_request_size: int = max_request_size
        self.max_upload_size: int = max_upload_size

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process Request And Check Size Limits.

        Arguments:
            request (Request): Incoming request.
            call_next: Next middleware or endpoint.

        Returns:
            Response: HTTP response.

        Raises:
            HTTPException: If request size exceeds limits.
        """

        content_length: str | None = request.headers.get("content-length")
        if content_length:
            content_length: int = int(content_length)
            content_type: str = request.headers.get("content-type", default="")

            if "multipart/form-data" in content_type:
                if content_length > self.max_upload_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload size {content_length} bytes exceeds maximum allowed {self.max_upload_size} bytes",  # noqa: E501
                    )
            elif content_length > self.max_request_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request size {content_length} bytes exceeds maximum allowed {self.max_request_size} bytes",
                )

        return await call_next(request)


__all__: list[str] = ["RequestSizeLimitMiddleware"]
