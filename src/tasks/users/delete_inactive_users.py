# Third-Party Imports
from asgiref.sync import async_to_sync
from celery import shared_task

# Local Imports
from config.mongodb import get_mongodb
from src.models.users import User


# Delete Inactive Users Task
@shared_task(bind=True)
def delete_inactive_users_task(self) -> None:
    """
    Periodic Task to Delete Inactive Users

    Deletes users who:
    - Registered More Than 30 Minutes Ago
    - Never Activated Their Account

    Runs Every 15 Minutes via Celery Beat
    """

    # Delete Inactive Users Async
    async def _delete_inactive_users_async() -> None:
        # Get MongoDB Connection
        async with get_mongodb() as db:
            # Get Users Collection
            collection = db.get_collection("users")

            # Delete Inactive Users
            await User.delete_inactive_users(collection)

    try:
        # Run the Async Logic in a Synchronous Context
        async_to_sync(_delete_inactive_users_async)()

    except Exception as e:
        # Retry Task
        raise self.retry(exc=e) from e


# Exports
__all__: list[str] = ["delete_inactive_users_task"]
