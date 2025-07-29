# Standard Library Imports
import asyncio
import contextlib
from typing import Any

# Third-Party Imports
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, worker_process_shutdown

# Local Imports
from config.mongodb import get_mongodb_manager
from config.settings import settings
from src.tasks.profiles import delete_profile_task  # noqa: F401
from src.tasks.users import delete_inactive_users_task  # noqa: F401

# Get MongoDB Manager Instance
mongodb_manager = get_mongodb_manager()


# Initialize Celery Application
def create_celery_app() -> Celery:
    """
    Create Celery App

    This Function Initializes and Configures the Celery Application.

    Returns:
        Celery: Configured Celery application instance.
    """

    # Set Default Configuration
    celery_app: Celery = Celery(
        main=settings.PROJECT_NAME,
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    # Update Configuration
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry_on_startup=True,
    )

    # Register Tasks
    celery_app.autodiscover_tasks(["src.tasks"])

    # Return Configured Application
    return celery_app


# Create Celery Application Instance
celery_app: Celery = create_celery_app()

# Configure Periodic Tasks
celery_app.conf.beat_schedule = {
    "delete-inactive-users": {
        "task": "src.tasks.users.delete_inactive_users.delete_inactive_users_task",
        "schedule": crontab(minute="*/5"),
        "options": {"expires": 60 * 10},
    },
}


# Initialize MongoDB Manager in Worker Process
@worker_process_init.connect
def init_worker(**kwargs: dict[str, Any]) -> None:
    """Initialize Worker Process with Fresh MongoDB Connections"""

    with contextlib.suppress(Exception):
        # Get MongoDB Manager Instance
        mongodb_manager.reset_connections()


# Clean up MongoDB Connections when Worker Shuts Down
@worker_process_shutdown.connect
def shutdown_worker(**kwargs: dict[str, Any]) -> None:
    """Clean up MongoDB Connections when Worker Shuts Down"""

    with contextlib.suppress(Exception):
        # If Event Loop is Running
        if asyncio.get_event_loop().is_running():
            # Close All MongoDB Connections Asynchronously
            close_task = asyncio.create_task(mongodb_manager.close_all())

            # Wait for The Task to Complete
            asyncio.get_event_loop().run_until_complete(close_task)

        else:
            # Run MongoDB Connection Closure
            asyncio.run(mongodb_manager.close_all())


# Exports
__all__: list[str] = ["celery_app"]
