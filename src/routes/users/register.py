# Third-Party Imports
import datetime
import logging

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_mongodb
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User, UserRegisterRequest, UserResponse

# Create Logger
logger = logging.getLogger(__name__)


# Register User
async def register_user_hander(request: UserRegisterRequest) -> JSONResponse:
    """
    Register a New User

    Args:
        request: UserRegisterRequest Containing User Registration Data

    Returns:
        JSONResponse: UserResponse with User Data

    Raises:
        HTTPException: For Validation Errors or Conflicts
    """

    # Get Database
    async with get_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

    # Check if user already exists
    existing_user: User | None = await User.get_by_identifier(
        collection=mongo_collection,
        identifier=request.username,
    ) or await User.get_by_identifier(
        collection=mongo_collection,
        identifier=request.email,
    )

    # If User Already Exists
    if existing_user:
        # Return Conflict Response
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "User With This Username or Email Already Exists"},
        )

    # Create and Validate User
    user: User = User(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        password=request.password,
    )

    # This Will Validate Password Complexity and Hash It
    user.set_password(password=request.password)

    # Save to Database
    await user.create(collection=mongo_collection, user_data=user.model_dump(by_alias=True))

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(datetime.UTC)

    # Generate Activation Token
    activation_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": current_time + datetime.timedelta(seconds=settings.ACTIVATION_JWT_EXPIRE),
        },
        key=settings.ACTIVATION_JWT_SECRET,
        algorithm=settings.ACTIVATION_JWT_ALGORITHM,
    )

    # Set Activation Token in Redis
    await redis_manager.set(
        key=f"activation_token:{user.id}",
        value=activation_token,
        expire=settings.ACTIVATION_JWT_EXPIRE,
        db=settings.REDIST_TOKEN_CACHE_DB,
    )

    # Dump User Data
    user_dump: dict = user.model_dump()

    # Remove Password from User Data
    user_dump.pop("password")

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=UserResponse(**user_dump).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["register_user_hander"]
