-- Create Keyspace for Celery Results
CREATE KEYSPACE IF NOT EXISTS celery_results
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};
