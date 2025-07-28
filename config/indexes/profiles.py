# Third-Party Imports
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import PyMongoError

# Local Imports
from config.mongodb import get_async_mongodb


async def create_profiles_indexes() -> None:
    """
    Asynchronously creates indexes for the 'profiles' collection in MongoDB.

    This function ensures that the 'profiles' collection has the necessary indexes
    for efficient data retrieval and to enforce data integrity.
    Indexes created:
    - 'user_id': Unique index to ensure each user has only one profile.
    - 'phone_number': Non-unique index for efficient lookup by phone number.
    - 'country': Non-unique index for efficient lookup by country.
    - 'updated_at': Non-unique index for efficient sorting and filtering by update time.

    Raises:
        PyMongoError: If there is an error during index creation.
    """

    # Get Database
    async with get_async_mongodb() as db:
        # Get profiles collection
        collection: AsyncCollection = db.get_collection("profiles")

        try:
            # Create Single Field Unique Index
            await collection.create_index("user_id", unique=True)

            # Create Single Field Non-Unique Indexes
            await collection.create_index("phone_number")
            await collection.create_index("country")
            await collection.create_index("updated_at")

        except PyMongoError as e:
            # Raise PyMongoError
            msg: str = f"Profile Index Creation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e
