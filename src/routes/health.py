# Standard Library Imports
from typing import Any

# Third-Party Imports
from fastapi import APIRouter, status

# Local Imports
from src.models.health import HealthResponse

# Initialize Router
router = APIRouter(
    prefix="/health",
    tags=["Health Check"],
)


# Health Check Endpoint
@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Health Check Endpoint",
    description="This Endpoint Returns the Status of the API.",
    name="Health Check",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "Successful Health Check",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "app": "InitStack",
                        "version": "1.0.0",
                        "environment": "development",
                    },
                },
            },
        },
    },
)
async def health_check() -> dict[str, Any]:
    """
    Health Check Endpoint

    This Function Returns the Status of the API.

    Returns:
        dict[str, Any]: Status information about the API.
    """

    # Return Health Response
    return HealthResponse.get_health_response()


# Exports
__all__: list[str] = ["router"]
