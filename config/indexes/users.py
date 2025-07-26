# Third-Party Imports
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import PyMongoError

# Local Imports
from config.mongodb import get_async_mongodb


async def create_users_indexes() -> None:
    # Get Database
    async with get_async_mongodb() as db:
        # Get users collection
        collection: AsyncCollection = db.get_collection("users")

        try:
            # Create Single Field Indexes
            await collection.create_index("username", unique=True)
            await collection.create_index("email", unique=True)

            # Create Status Compound Index
            await collection.create_index([("is_active", 1), ("is_staff", 1), ("is_superuser", 1)])

            # Create Date Indexes
            await collection.create_index("date_joined")
            await collection.create_index("last_login")
            await collection.create_index("updated_at")

        except PyMongoError as e:
            # Raise PyMongoError
            msg: str = f"Index Creation Failed: {e!s}"

            # Raise PyMongoError
            raise PyMongoError(msg) from e
