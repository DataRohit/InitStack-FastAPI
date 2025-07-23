# Third-Party Imports
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_mongodb
from config.settings import settings
from src.models.users.base import User

# JWT Token Security Scheme
security = HTTPBearer()


# Validate JWT Token Function
def _validate_jwt_token(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Validate JWT Token

    This Function Validates the JWT Access Token
    From the Authorization Header.

    Args:
        credentials (HTTPAuthorizationCredentials): The Credentials Containing the JWT Token

    Returns:
        str: The User ID if Token is Valid

    Raises:
        HTTPException: If Token is Invalid
    """

    # Validate Token
    try:
        # Decode Token
        payload: dict = jwt.decode(
            jwt=credentials.credentials,
            key=settings.ACCESS_JWT_SECRET,
            algorithms=[settings.ACCESS_JWT_ALGORITHM],
            verify=True,
            audience=settings.PROJECT_NAME,
            issuer=settings.PROJECT_NAME,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
                "strict_aud": True,
            },
        )

    except jwt.InvalidTokenError as e:
        # Raise 401 Unauthorized Error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication Credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Return User ID
    return payload["sub"]


# Get Current User Function
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:  # noqa: B008
    """
    Get Current User

    This Function Extracts and Validates the JWT Token
    from the Authorization Header and Returns the User Data.

    Args:
        credentials (HTTPAuthorizationCredentials): The Credentials Containing the JWT Token

    Returns:
        User: The User Data from the Validated Token

    Raises:
        HTTPException: If Token is Invalid or User Not Found
    """

    # Validate Token
    user_id: str = _validate_jwt_token(credentials)

    # Get User from Database
    async with get_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Get User by ID
        user: dict | None = await mongo_collection.find_one(filter={"_id": user_id})

    # If User Does Not Exist
    if user is None:
        # Raise 404 Not Found Error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User Not Found"},
        )

    # Return User
    return User(**user)


# Exports
__all__: list[str] = ["get_current_user"]
