# Third-Party Imports
from celery import Celery
from celery.schedules import crontab

# Local Imports
from config.settings import settings

# Imports Tasks
from src.tasks.users import delete_inactive_users_task  # noqa: F401


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
        "schedule": crontab(minute="*/15"),
        "options": {"expires": 60 * 10},
    },
}

# Exports
__all__: list[str] = ["celery_app"]
