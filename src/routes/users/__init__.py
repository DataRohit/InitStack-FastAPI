# Local Imports
from src.routes.users.base import router as base_router
from src.routes.users.register import router as register_router

# Combine Routers
router = base_router
router.include_router(register_router)

# Exports
__all__: list[str] = ["router"]
