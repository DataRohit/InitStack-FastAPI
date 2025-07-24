# Third-Party Imports
from fastapi import status
from fastapi.responses import JSONResponse

# Local Imports
from src.models.users import User, UserResponse


# Get Current User Route
def get_current_user_handler(current_user: User) -> JSONResponse:
    """
    Get Current User

    Returns the currently authenticated user's data.

    Args:
        current_user (User): The authenticated user from dependency

    Returns:
        JSONResponse: User data with 200 status
    """

    # If User Is Not Active
    if not current_user.is_active:
        # Return Conflict Response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User Is Not Active"},
        )

    # Prepare Response Data
    response_data: dict = {key: value for key, value in current_user.model_dump().items() if key != "password"}

    # Return User Data
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["get_current_user_handler"]
