# Local Imports
from config.middlewares.cors import add_cors_middleware
from config.middlewares.https_redirect import add_https_redirect_middleware
from config.middlewares.security_headers import add_security_headers_middleware
from config.middlewares.trusted_host import add_trusted_host_middleware

# Exports
__all__: list[str] = [
    "add_cors_middleware",
    "add_https_redirect_middleware",
    "add_security_headers_middleware",
    "add_trusted_host_middleware",
]
