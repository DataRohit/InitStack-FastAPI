# Standard Library Imports
import datetime

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection

# Local Imports
from config.mongodb import get_async_mongodb
from config.redis_cache import get_async_redis
from config.settings import settings
from src.models.users import User
from src.models.users.login import UserLoginRequest, UserLoginResponse


# Internal Function to Check If New Access & Refresh Token Are Required
async def _check_if_new_tokens_required(user: User) -> dict:
    """
    Check If New Access & Refresh Token Are Required

    Args:
        user (User): User Instance

    Returns:
        (bool, bool): True If New Access & Refresh Token Are Required, False Otherwise
    """

    # Set Default Flags
    is_new_access_token_required: bool = True
    is_new_refresh_token_required: bool = True

    # Set Key for Access Token & Refresh Token Cache
    access_token_key: str = f"access_token:{user.id}"
    refresh_token_key: str = f"refresh_token:{user.id}"

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Get Access Token & Refresh Token from Redis
        access_token: str | None = await redis.get(access_token_key)
        refresh_token: str | None = await redis.get(refresh_token_key)

    # If Access Token Is Cached
    if access_token:
        try:
            # Decode Access Token
            jwt.decode(
                jwt=access_token,
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

            # Set Flag to False
            is_new_access_token_required = False

        except jwt.InvalidTokenError:
            # Set Flag to True
            is_new_access_token_required = True

    # If Refresh Token Is Cached
    if refresh_token:
        try:
            # Decode Refresh Token
            jwt.decode(
                jwt=refresh_token,
                key=settings.REFRESH_JWT_SECRET,
                algorithms=[settings.REFRESH_JWT_ALGORITHM],
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

            # Set Flag to False
            is_new_refresh_token_required = False

        except jwt.InvalidTokenError:
            # Set Flag to True
            is_new_refresh_token_required = True

    # Return Tokens & Flags
    return {
        "access_token": {
            "token": access_token,
            "regenerate": is_new_access_token_required,
        },
        "refresh_token": {
            "token": refresh_token,
            "regenerate": is_new_refresh_token_required,
        },
    }


# Internal Function to Generate Access Token
async def _generate_access_token(user: User) -> str:
    """
    Generate Access Token

    Args:
        user (User): User Instance

    Returns:
        str: Access Token
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.ACCESS_JWT_EXPIRE)

    # Generate Access Token
    access_token: str = jwt.encode(
        payload={
            "sub": str(user.id),
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.ACCESS_JWT_SECRET,
        algorithm=settings.ACCESS_JWT_ALGORITHM,
    )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Set Access Token in Redis
        await redis.set(
            f"access_token:{user.id}",
            value=access_token,
            ex=settings.ACCESS_JWT_EXPIRE,
        )

    # Return Access Token
    return access_token


# Internal Function to Generate Refresh Token
async def _generate_refresh_token(user: User) -> str:
    """
    Generate Refresh Token

    Args:
        user (User): User Instance

    Returns:
        str: Refresh Token
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.REFRESH_JWT_EXPIRE)

    # Generate Refresh Token
    refresh_token: str = jwt.encode(
        payload={
            "sub": str(user.id),
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
        },
        key=settings.REFRESH_JWT_SECRET,
        algorithm=settings.REFRESH_JWT_ALGORITHM,
    )

    # Get Async Redis Adapter
    async with get_async_redis(db=settings.REDIS_TOKEN_CACHE_DB) as redis:
        # Set Refresh Token in Redis
        await redis.set(
            f"refresh_token:{user.id}",
            value=refresh_token,
            ex=settings.REFRESH_JWT_EXPIRE,
        )

    # Return Refresh Token
    return refresh_token


# Login User
async def login_user_handler(request: UserLoginRequest) -> JSONResponse:
    """
    Login a User

    Args:
        request (UserLoginRequest): UserLoginRequest Containing User Login Data

    Returns:
        JSONResponse: UserResponse with User Data
    """

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Get User by Username or Email
        existing_user: dict | None = await mongo_collection.find_one(
            filter={
                "$or": [
                    {"username": request.identifier},
                    {"email": request.identifier},
                ],
            },
        )

        # If User Does Not Exist
        if not existing_user:
            # Return Not Found Response
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User Not Found"},
            )

        # If User Date Joined & Updated At Are Same
        if existing_user["date_joined"] == existing_user["updated_at"]:
            # Return Conflict Response
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "User Account Has Not Been Activated"},
            )

        # If User Is Not Active
        if not existing_user["is_active"]:
            # Calculated Updated At
            updated_at: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

            # Activate User
            await mongo_collection.update_one(
                filter={"_id": existing_user["_id"]},
                update={
                    "$set": {
                        "is_active": True,
                        "updated_at": updated_at,
                    },
                },
            )

            # Update User
            existing_user["is_active"] = True
            existing_user["updated_at"] = updated_at

        # Create and Validate User
        user: User = User(**existing_user)

        # Validate Password
        if not user.verify_password(password=request.password):
            # Return Unauthorized Response
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Password"},
            )

        # Check If New Access & Refresh Token Are Required
        tokens: dict = await _check_if_new_tokens_required(user=user)

        # Extract Tokens
        access_token: str = tokens["access_token"]["token"]
        refresh_token: str = tokens["refresh_token"]["token"]

        # If New Access Token Is Required
        if tokens["access_token"]["regenerate"]:
            # Generate New Access Token
            access_token = await _generate_access_token(user=user)

        # If New Refresh Token Is Required
        if tokens["refresh_token"]["regenerate"]:
            # Generate New Refresh Token
            refresh_token = await _generate_refresh_token(user=user)

        # Calculate Last Login
        last_login: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

        # Update User Last Login
        await mongo_collection.update_one(
            filter={"_id": user.id},
            update={"$set": {"last_login": last_login}},
        )

    # Update User Login in User Instance
    user.last_login = last_login

    # Prepare Response Data
    response_data: dict = {
        "user": {key: value for key, value in user.model_dump().items() if key != "password"},
        "access_token": {
            "token": access_token,
            "type": "bearer",
            "expires_in": settings.ACCESS_JWT_EXPIRE,
        },
        "refresh_token": {
            "token": refresh_token,
            "expires_in": settings.REFRESH_JWT_EXPIRE,
        },
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UserLoginResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["login_user_handler"]
