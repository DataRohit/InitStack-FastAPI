# ruff: noqa: F401

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange
from kombu import Queue

from config.settings import settings

celery_app: Celery = Celery(
    "initstack",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_acks_late=settings.celery_task_acks_late,
    task_reject_on_worker_lost=settings.celery_task_reject_on_worker_lost,
    result_expires=settings.celery_result_expires,
    result_persistent=settings.celery_result_persistent,
    result_compression=settings.celery_result_compression,
    broker_connection_retry=settings.celery_broker_connection_retry,
    broker_connection_retry_on_startup=settings.celery_broker_connection_retry_on_startup,
    broker_connection_max_retries=settings.celery_broker_connection_max_retries,
    elasticsearch_save_meta_as_text=False,
    elasticsearch_retry_on_timeout=True,
    elasticsearch_max_retries=3,
    elasticsearch_timeout=30,
)

celery_app.conf.task_queues = (
    Queue(
        "default",
        Exchange("default", type="direct"),
        routing_key="default",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "high_priority",
        Exchange("high_priority", type="direct"),
        routing_key="high_priority",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "low_priority",
        Exchange("low_priority", type="direct"),
        routing_key="low_priority",
        queue_arguments={"x-max-priority": 10},
    ),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

celery_app.conf.task_routes = {
    "src.tasks.email.*": {"queue": "high_priority"},
    "src.tasks.reports.*": {"queue": "low_priority"},
}

celery_app.conf.beat_schedule = {
    "health-check-every-minute": {
        "task": "src.tasks.health.check_system_health",
        "schedule": crontab(minute="*"),
        "options": {"queue": "default"},
    },
    "cleanup-old-results-daily": {
        "task": "src.tasks.maintenance.cleanup_old_results",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "low_priority"},
    },
}

try:
    import src.tasks.health
    import src.tasks.maintenance
except ImportError:
    pass


__all__: list[str] = ["celery_app"]
