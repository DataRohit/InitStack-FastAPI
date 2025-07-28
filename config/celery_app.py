# Third-Party Imports
from cassandra.cluster import EXEC_PROFILE_DEFAULT, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy
from celery import Celery
from celery.schedules import crontab

# Local Imports
from config.settings import settings
from src.tasks.profiles import delete_profile_task  # noqa: F401
from src.tasks.users import delete_inactive_users_task  # noqa: F401

# Execution Profile
my_e_profile = ExecutionProfile(
    load_balancing_policy=DCAwareRoundRobinPolicy(
        local_dc=settings.CASSANDRA_DC,
    ),
)


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
        cassandra_servers=[f"{settings.CASSANDRA_HOST}"],
        cassandra_port=settings.CASSANDRA_PORT,
        cassandra_keyspace=settings.CASSANDRA_KEYSPACE,
        cassandra_table="celery_taskmeta",
        cassandra_read_consistency="LOCAL_QUORUM",
        cassandra_write_consistency="LOCAL_QUORUM",
        cassandra_entry_ttl=60 * 60 * 24,
        cassandra_auth_provider="PlainTextAuthProvider",
        cassandra_auth_kwargs={
            "username": settings.CASSANDRA_USER,
            "password": settings.CASSANDRA_PASS,
        },
        cassandra_options={
            "cql_version": settings.CASSANDRA_CQL_VERSION,
            "protocol_version": settings.CASSANDRA_PROTOCOL_VERSION,
            "execution_profiles": {EXEC_PROFILE_DEFAULT: my_e_profile},
        },
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

# Exports
__all__: list[str] = ["celery_app"]
