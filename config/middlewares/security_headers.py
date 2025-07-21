# Third-Party Imports
from fastapi import FastAPI
from starlette.types import Message, Receive, Scope, Send


# Security Headers Middleware
class SecurityHeadersMiddleware:
    """
    Security Headers Middleware Class

    This Middleware Adds Various Security Headers To All HTTP Responses
    To Enhance The Security Of The Application.
    """

    # Initialize Security Headers Middleware
    def __init__(self, app: FastAPI) -> None:
        """
        This Function Initializes The Security Headers Middleware.

        Args:
            app (FastAPI): The FastAPI Application Instance
        """

        # Initialize FastAPI Application
        self.app: FastAPI = app

    # Process The Request And Add Security Headers To The Response
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        This Function Processes The Request And Adds Security Headers To The Response.

        Args:
            scope (Scope): The FastAPI Scope
            receive (Receive): The FastAPI Receive Callable
            send (Send): The FastAPI Send Callable
        """

        # If The Scope Is Not HTTP
        if scope["type"] != "http":
            # Call The Next Middleware
            await self.app(scope, receive, send)

            # Return
            return

        # Add Security Headers To The Response
        async def send_with_headers(message: Message) -> None:
            """
            Send With Headers Function

            This Function Sends The Message With Security Headers.

            Args:
                message (Message): The FastAPI Message
            """

            # If The Message Type Is HTTP Response Start
            if message["type"] == "http.response.start":
                # Convert Headers To Dictionary
                headers = dict(message.get("headers", []))

                # Security Headers
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"content-security-policy": b"default-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; style-src 'self' https://cdn.jsdelivr.net; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline';",  # noqa: E501
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                }

                # Traverse Security Headers
                for header, value in security_headers.items():
                    # If The Header Is Not In The Headers
                    if header not in headers:
                        # Add The Header
                        headers[header] = value

                # Convert Headers Back To List Of Tuples
                message["headers"] = list(headers.items())

            # Send The Message
            await send(message)

        # Call The Next Middleware
        await self.app(scope, receive, send_with_headers)


# Add Security Headers Middleware Function
def add_security_headers_middleware(app: FastAPI) -> None:
    """
    Add Security Headers Middleware Function

    This Function Adds Security Headers Middleware To The Provided FastAPI Application.

    Args:
        app (FastAPI): The FastAPI Application Instance
    """

    # Add Security Headers Middleware
    app.add_middleware(middleware_class=SecurityHeadersMiddleware)
