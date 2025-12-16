from fastapi import APIRouter

from src.controllers import consul_controller
from src.controllers import health_controller
from src.controllers import rate_limit_controller
from src.controllers import redis_controller


def create_api_router() -> APIRouter:
    """Create Main API Router With All Route Modules.

    Arguments:
        None

    Returns:
        APIRouter: Configured main API router with all controller routes.

    Raises:
        None
    """

    main_router: APIRouter = APIRouter(prefix="/api/v1")

    main_router.include_router(router=health_controller.router)
    main_router.include_router(router=consul_controller.router)
    main_router.include_router(router=redis_controller.router)
    main_router.include_router(router=rate_limit_controller.router)

    return main_router


__all__: list[str] = ["create_api_router"]
