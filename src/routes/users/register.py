# Third-Party Imports
import datetime
from pathlib import Path

# Third-Party Imports
import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import InsertOneResult

# Local Imports
from config.mailer import render_template, send_email
from config.mongodb import get_mongodb
from config.redis import redis_manager
from config.settings import settings
from src.models.users import User, UserRegisterRequest, UserResponse


# Internal Function to Send Activation Email
async def _send_activation_email(user: User) -> None:
    """
    Send Activation Email

    Args:
        user (User): User Instance
    """

    # Get Current Time
    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    # Calculate Expiry Time
    expiry_time: datetime.datetime = current_time + datetime.timedelta(seconds=settings.ACTIVATION_JWT_EXPIRE)

    # Generate Activation Token
    activation_token: str = jwt.encode(
        payload={
            "sub": user.id,
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
            "iat": current_time,
            "exp": expiry_time,
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

    # Create Activation Link
    activation_link: str = f"{settings.PROJECT_DOMAIN}/api/users/activate?token={activation_token}"

    # Prepare Email Context
    email_context: dict = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "activation_link": activation_link,
        "activation_link_expiry": expiry_time.isoformat(),
        "current_year": current_time.year,
        "project_name": settings.PROJECT_NAME,
    }

    # Set Email Template Path
    template_path: str = str(Path(__file__).parent.parent.parent / "templates" / "users" / "registered.html")

    # Render Email Template
    html_content: str = await render_template(template_path, email_context)

    # Send Email
    await send_email(
        to_email=user.email,
        subject=f"Activate Your {settings.PROJECT_NAME} Account",
        html_content=html_content,
    )


# Register User
async def register_user_handler(request: UserRegisterRequest) -> JSONResponse:
    """
    Register a New User

    Args:
        request (UserRegisterRequest): UserRegisterRequest Containing User Registration Data

    Returns:
        JSONResponse: UserResponse with User Data
    """

    # Get Database and Collection
    async with get_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("users")

        # Check If User Already Exists
        existing_user: dict | None = await mongo_collection.find_one(
            filter={
                "$or": [
                    {"username": request.username},
                    {"email": request.email},
                ],
            },
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
        result: InsertOneResult | None = await mongo_collection.insert_one(
            document=user.model_dump(by_alias=True),
        )

        # If Insertion Failed
        if not result:
            # Return Internal Server Error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to Register User"},
            )

    # Send Activation Email
    await _send_activation_email(user=user)

    # Prepare Response Data
    response_data: dict = {key: value for key, value in user.model_dump().items() if key != "password"}

    # Return Response with UserResponse Model
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=UserResponse(**response_data).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = ["register_user_handler"]
