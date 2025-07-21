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

        CORS_ORIGINS (str): List of CORS Origins
        CORS_CREDENTIALS (bool): CORS Credentials Flag
        CORS_METHODS (str): List of CORS Methods
        CORS_HEADERS (str): List of CORS Headers
        CORS_MAX_AGE (int): CORS Max Age

        CELERY_BROKER_URL (str): Celery Broker URL (RabbitMQ)
        CELERY_RESULT_BACKEND (str): Celery Result Backend URL

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
    PROJECT_DESCRIPTION: str = "A FastAPI Server for the InitStack Project"
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

    # Celery Configuration
    CELERY_BROKER_URL: str = "amqp://NGeDFwAgoZwmMvP:ftT4tT0Qy2cQXGm@rabbitmq-service:5672//"
    CELERY_RESULT_BACKEND: str = "db+postgresql://wIym6FbBxLhvf9p:Xm5XGvwnwSuJxtl@postgres-service:5432/celery_results"

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
