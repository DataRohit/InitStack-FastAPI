# Third-Party Imports
from pydantic_settings import BaseSettings


# Settings Class
class Settings(BaseSettings):
    """
    Settings Class

    This Class is Used to Load Environment Variables.

    Attributes:
        APP_ENV (str): Application Environment (development, production, etc.)
        DEBUG (bool): Debug Mode
        HOST (str): Host Address
        PORT (int): Port Number
        RELOAD (bool): Reload Mode

        API_PREFIX (str): API Prefix
        PROJECT_NAME (str): Project Name
        PROJECT_SUMMARY (str): Project Summary
        PROJECT_DESCRIPTION (str): Project Description
        VERSION (str): Project Version
        PROJECT_WEBSITE (str): Project Website
        PROJECT_EMAIL (str): Project Email
        LICENSE_URL (str): Project License URL

        CORS_ORIGINS (str): List of CORS Origins
        CORS_CREDENTIALS (bool): CORS Credentials Flag
        CORS_METHODS (str): List of CORS Methods
        CORS_HEADERS (str): List of CORS Headers
        CORS_MAX_AGE (int): CORS Max Age

        ALLOWED_HOSTS (str): List of Allowed Hosts

        COMPRESSION_MIN_SIZE (int): Minimum Response Size (bytes) to Compress
        COMPRESSION_LEVEL (int): GZip Compression Level (1-9)

        CELERY_BROKER_URL (str): Celery Broker URL (RabbitMQ)
        CELERY_RESULT_BACKEND (str): Celery Result Backend URL

        REDIS_URL (str): Redis Server URL
        REDIS_HTTP_RATE_LIMIT_DB (int): Redis Database Number for HTTP Rate Limiting

        RATE_LIMIT (int): Default Maximum Requests Per Window
        RATE_LIMIT_WINDOW (int): Default Rate Limit Window in Seconds

    Configuration:
        env_file (str): Environment File
        env_file_encoding (str): Environment File Encoding
    """

    # Server Configuration
    APP_ENV: str = "production"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False

    # API Configuration
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "InitStack FastAPI Server"
    PROJECT_SUMMARY: str = "A FastAPI Server for the InitStack Project"
    PROJECT_DESCRIPTION: str = "A Production-Ready Full-Stack Starter Kit With FastAPI Backend, Celery Task Queue, And Comprehensive DevOps Tooling"  # noqa: E501
    VERSION: str = "0.1.0"
    PROJECT_WEBSITE: str = "https://github.com/InitStack/InitStack"
    PROJECT_EMAIL: str = "initstack@protonmail.com"
    LICENSE_URL: str = "https://github.com/InitStack/InitStack/blob/master/license"

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    CORS_HEADERS: str = "*"
    CORS_MAX_AGE: int = 600

    # Security Configuration
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # Compression Settings
    COMPRESSION_MIN_SIZE: int = 1024
    COMPRESSION_LEVEL: int = 6

    # Celery Configuration
    CELERY_BROKER_URL: str = "amqp://NGeDFwAgoZwmMvP:ftT4tT0Qy2cQXGm@rabbitmq-service:5672//"
    CELERY_RESULT_BACKEND: str = "db+postgresql://wIym6FbBxLhvf9p:Xm5XGvwnwSuJxtl@postgres-service:5432/celery_results"

    # Redis Configuration
    REDIS_URL: str = "redis://:WFyzhcO3ByZIjdd@redis-service:6379/"
    REDIS_HTTP_RATE_LIMIT_DB: int = 0

    # Rate Limit Configuration
    RATE_LIMIT: int = 60
    RATE_LIMIT_WINDOW: int = 60

    # Configuration
    class Config:
        """
        Configuration Class

        This Class is Used to Load Environment Variables.

        Attributes:
            env_file (str): Environment File
            env_file_encoding (str): Environment File Encoding
        """

        # Environment File
        env_file: str = ".env"

        # Environment File Encoding
        env_file_encoding: str = "utf-8"


# Initialize Settings
settings: Settings = Settings()

# Exports
__all__: list[str] = ["settings"]
