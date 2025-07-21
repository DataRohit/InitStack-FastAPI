# Local Imports
from src.routes.health import router as health_router
from src.routes.users import router as users_router

# Exports
__all__: list[str] = ["health_router", "users_router"]
