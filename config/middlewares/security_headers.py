# Third-Party Imports
from starlette.types import ASGIApp, Message, Receive, Scope, Send


# Security Headers Middleware
class SecurityHeadersMiddleware:
    """
    Security Headers Middleware Class

    This Middleware Adds Various Security Headers To All HTTP Responses
    To Enhance The Security Of The Application.
    """

    # Initialize Security Headers Middleware
    def __init__(self, app: ASGIApp) -> None:
        """
        This Function Initializes The Security Headers Middleware.

        Args:
            app (ASGIApp): The ASGI Application Instance.
        """

        # Initialize ASGI Application
        self.app: ASGIApp = app

    # Process The Request And Add Security Headers To The Response
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        This Function Processes The Request And Adds Security Headers To The Response.

        Args:
            scope (Scope): The ASGI Scope.
            receive (Receive): The ASGI Receive Callable.
            send (Send): The ASGI Send Callable.
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
                message (Message): The ASGI Message.
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
                    b"content-security-policy": b"default-src 'self'",
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
def add_security_headers_middleware(app: ASGIApp) -> None:
    """
    Add Security Headers Middleware Function

    This Function Adds Security Headers Middleware To The Provided ASGI Application.

    Args:
        app (ASGIApp): The ASGI Application Instance.
    """

    # Add Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)
