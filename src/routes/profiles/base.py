# Third-Party Imports
from fastapi import APIRouter, status

# Initialize Router
router = APIRouter(
    prefix="/users/profiles",
    tags=["Profiles"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
)


# Exports
__all__: list[str] = [
    "router",
]
