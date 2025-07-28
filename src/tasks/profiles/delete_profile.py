# Third-Party Imports
from celery import shared_task
from pymongo.collection import Collection

# Local Imports
from config.mongodb import get_sync_mongodb


# Delete Profile Task
@shared_task(bind=True)
def delete_profile_task(self, user_id: str) -> None:
    """
    Task to Delete a User Profile

    Deletes the profile associated with the given user_id.
    This task can be run on demand.

    Args:
        user_id (str): The unique identifier of the user whose profile is to be deleted.
    """

    try:
        # Get MongoDB Connection using context manager
        with get_sync_mongodb() as db:
            # Get Profiles Collection
            collection: Collection = db.get_collection("profiles")

            # Delete the Profile
            collection.delete_one(filter={"user_id": user_id})

    except Exception as e:
        # Log the error and retry the task
        raise self.retry(exc=e) from e


# Exports
__all__: list[str] = ["delete_profile_task"]
