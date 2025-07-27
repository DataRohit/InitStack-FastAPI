# Standard Library Imports
import datetime

# Third-Party Imports
from celery import shared_task
from pymongo.collection import Collection

# Local Imports
from config.mongodb import get_sync_mongodb


# Delete Inactive Users Task
@shared_task(bind=True)
def delete_inactive_users_task(self) -> None:
    """
    Periodic Task to Delete Inactive Users

    Deletes users who:
    - Registered More Than 30 Minutes Ago
    - Never Activated Their Account

    Runs Every 5 Minutes via Celery Beat
    """

    try:
        # Get MongoDB Connection using context manager
        with get_sync_mongodb() as db:
            # Get Users Collection
            collection: Collection = db.get_collection("users")

            # Delete Inactive Users
            collection.delete_many(
                filter={
                    "date_joined": {
                        "$lt": (datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(minutes=30)),
                    },
                    "is_active": False,
                },
            )

    except Exception as e:
        # Retry Task
        raise self.retry(exc=e) from e


# Exports
__all__: list[str] = ["delete_inactive_users_task"]
