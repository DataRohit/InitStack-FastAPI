import datetime
from typing import Any

from elasticsearch import Elasticsearch

from config.celery_app import celery_app
from config.settings import settings


@celery_app.task(name="src.tasks.maintenance.cleanup_old_results")
def cleanup_old_results() -> dict[str, Any]:
    """
    Cleanup Old Celery Results From Elasticsearch.

    Args:
        None

    Returns:
        dict[str, Any]: Cleanup Summary.

    Raises:
        Exception: For Any Unexpected Errors During Cleanup.
    """

    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    cutoff_time: datetime.datetime = current_time - datetime.timedelta(
        seconds=settings.celery_result_expires,
    )

    es_client: Elasticsearch = Elasticsearch(
        hosts=settings.elasticsearch_hosts,
        basic_auth=(
            settings.elasticsearch_username,
            settings.elasticsearch_password,
        ),
        verify_certs=settings.elasticsearch_ssl_verify,
    )

    delete_response: dict[str, Any] = es_client.delete_by_query(
        index=f"{settings.celery_elasticsearch_index_prefix}-*",
        body={
            "query": {
                "range": {
                    "date_done": {
                        "lt": cutoff_time.isoformat(),
                    },
                },
            },
        },
    )

    es_client.close()

    return {
        "status": "completed",
        "timestamp": current_time.isoformat(),
        "cutoff_time": cutoff_time.isoformat(),
        "deleted_count": delete_response.get("deleted", 0),
    }


__all__: list[str] = ["cleanup_old_results"]
