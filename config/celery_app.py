# Third-Party Imports
from celery import Celery

# Local Imports
from config.settings import settings


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

    # Return Configured Application
    return celery_app


# Create Celery Application Instance
celery_app: Celery = create_celery_app()


# Exports
__all__: list[str] = ["celery_app"]
