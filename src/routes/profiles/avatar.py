# Standard Imports
import datetime
import io
from typing import Annotated

# Third-Party Imports
from fastapi import Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.results import UpdateResult

# Local Imports
from config.jwt_auth import get_current_user
from config.mongodb import get_async_mongodb
from config.s3_storage import get_sync_s3
from config.settings import settings
from src.models.profiles import Profile
from src.models.profiles.base import ProfileResponse
from src.models.users.base import User
from src.routes.profiles.base import router


# Convert Image to JPG
def _convert_image_to_jpg(image: UploadFile) -> bytes:
    """
    Convert Image to JPG

    Args:
        image (UploadFile): Image to Convert

    Returns:
        bytes: JPG Image

    Raises:
        ValueError: If Image is Invalid
    """

    try:
        # Read Image Data
        image_data: bytes = image.file.read()

        # Open Image
        img = Image.open(io.BytesIO(image_data))

        # If Image not RGB
        if img.mode != "RGB":
            # Convert to RGB
            img = img.convert("RGB")

        # Create Output Buffer
        output_buffer: io.BytesIO = io.BytesIO()

        # Save Image to Buffer with Optimization
        img.save(output_buffer, format="JPEG", quality=85, optimize=True)

        # Get Image Bytes
        return output_buffer.getvalue()

    except UnidentifiedImageError as e:
        # Set Error Message
        msg: str = "Invalid Image Format"

        # Raise ValueError
        raise ValueError(msg) from e

    finally:
        # Reset File Pointer for Potential Reuse
        image.file.seek(0)


# Upload Image to S3
def _upload_image_to_s3(image_data: bytes, current_user: User) -> str:
    """
    Upload Image to S3

    Args:
        image_data (bytes): Image Data
        current_user (User): Current Authenticated User

    Returns:
        str: S3 URL
    """

    # Generate S3 Key
    s3_key: str = f"profiles/avatars/{current_user.id}.jpg"

    # Get S3 Instance
    with get_sync_s3() as s3:
        # Upload Image to S3
        s3.upload_fileobj(
            Fileobj=io.BytesIO(image_data),
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=s3_key,
        )

    # Return S3 URL
    return f"{settings.MINIO_BASE_URL}/{settings.MINIO_BUCKET_NAME}/{s3_key}"


# Update Avatar Endpoint
@router.put(
    path="/avatar/update",
    status_code=status.HTTP_200_OK,
    summary="Update User Avatar",
    description="""
    Update User Avatar.

    This Endpoint Allows a Logged-in User to Update Their Avatar by Providing:
    - File (JPEG, JPG, PNG)
    """,
    name="Update Avatar",
    response_model=ProfileResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Avatar Updated Successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "Avatar Updated": {
                            "summary": "Avatar Updated Successfully",
                            "value": {
                                "id": "687ea9fa53bf34da640e4ef5",
                                "user_id": "687ea9fa53bf34da640e4ef5",
                                "first_name": "John",
                                "last_name": "Doe",
                                "username": "john_doe",
                                "email": "john_doe@example.com",
                                "phone_number": "1234567890",
                                "date_of_birth": "2000-01-01",
                                "gender": "male",
                                "avatar": "https://example.com/avatar.jpg",
                                "created_at": "2022-01-01T00:00:00.000Z",
                                "updated_at": "2022-01-01T00:00:00.000Z",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "examples": {
                        "No File Provided": {
                            "summary": "No File Provided",
                            "value": {
                                "detail": "No File Provided",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid Authentication Credentials",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "examples": {
                        "Authentication Required": {
                            "summary": "Authentication Required",
                            "value": {
                                "detail": "Authentication Required",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "examples": {
                        "Profile Not Found": {
                            "summary": "Profile Not Found",
                            "value": {
                                "detail": "Profile Not Found",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Unprocessable Entity",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Image Format": {
                            "summary": "Invalid Image Format",
                            "value": {
                                "detail": "Invalid Request",
                                "errors": [
                                    {
                                        "field": "file",
                                        "reason": "Invalid Image Format",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Update Failed": {
                            "summary": "Profile Update Failed",
                            "value": {
                                "detail": "Failed to Update Profile",
                            },
                        },
                    },
                },
            },
        },
    },
)
async def update_avatar(
    file: Annotated[UploadFile | None, File(description="Image file to upload (JPEG, JPG, PNG)")],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """
    Update User Avatar

    Args:
        file (UploadFile | None): Image file to upload (JPEG, JPG, PNG)
        current_user (User): Current authenticated user

    Returns:
        JSONResponse: ProfileResponse with updated avatar URL
    """

    # If No File Provided
    if not file:
        # Return Bad Request Response
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "No File Provided"},
        )

    try:
        # Convert Image to JPG
        image_data: bytes = _convert_image_to_jpg(file)

    except ValueError:
        # Return Unprocessable Entity Response
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Invalid Request",
                "errors": [
                    {
                        "field": "file",
                        "reason": "Invalid Image Format",
                    },
                ],
            },
        )

    # Upload Image to S3
    s3_url: str = _upload_image_to_s3(image_data, current_user)

    # Get Database and Collection
    async with get_async_mongodb() as db:
        # Get Collection
        mongo_collection: AsyncCollection = db.get_collection("profiles")

        # Prepare Update Data with Timestamp
        updated_at: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
        update_data: dict = {
            "avatar_url": s3_url,
            "updated_at": updated_at,
        }

        # Update Profile Avatar URL
        result: UpdateResult = await mongo_collection.update_one(
            filter={"user_id": current_user.id},
            update={"$set": update_data},
        )

        # If Update Failed (No Document Found or No Changes)
        if result.matched_count == 0:
            # Return Not Found Response
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Profile Not Found"},
            )

        # If No Changes Made
        if result.modified_count == 0:
            # Return Internal Server Error
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to Update Profile"},
            )

        # Get Updated Profile for Response
        updated_profile_data: dict | None = await mongo_collection.find_one(
            filter={"user_id": current_user.id},
        )

    # Create Profile Instance for Response
    profile: Profile = Profile(**updated_profile_data)

    # Return Response with ProfileResponse Model
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ProfileResponse(**profile.model_dump()).model_dump(mode="json"),
    )


# Exports
__all__: list[str] = [
    "update_avatar",
]
