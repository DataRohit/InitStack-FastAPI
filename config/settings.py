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
        PROJECT_DOMAIN (str): Project Domain
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

        OTLP_HTTP_ENDPOINT (str): OpenTelemetry HTTP Endpoint
        OTLP_SERVICE_ID (str): OpenTelemetry Service ID

        CELERY_BROKER_URL (str): Celery Broker URL (RabbitMQ)
        CELERY_RESULT_BACKEND (str): Celery Result Backend

        CASSANDRA_HOST (str): Cassandra Host
        CASSANDRA_PORT (int): Cassandra Port
        CASSANDRA_USER (str): Cassandra User
        CASSANDRA_PASS (str): Cassandra Password
        CASSANDRA_KEYSPACE (str): Cassandra Keyspace

        REDIS_URL (str): Redis Server URL
        REDIS_HOST (str): Redis Host
        REDIS_PORT (int): Redis Port
        REDIS_USER (str): Redis User
        REDIS_PASS (str): Redis Password
        REDIS_HTTP_RATE_LIMIT_DB (int): Redis Database Number for HTTP Rate Limiting
        REDIST_TOKEN_CACHE_DB (int): Redis Database Number for Token Caching

        RATE_LIMIT (int): Default Maximum Requests Per Window
        RATE_LIMIT_WINDOW (int): Default Rate Limit Window in Seconds

        HTTP_MAX_CONNECTIONS (int): Maximum Number of HTTP Connections
        HTTP_KEEPALIVE_CONNECTIONS (int): Maximum Number of Keep-Alive Connections
        HTTP_KEEPALIVE_EXPIRY (int): Keep-Alive Expiry Time in Seconds
        HTTP_TIMEOUT_CONNECT (float): HTTP Connection Timeout in Seconds
        HTTP_TIMEOUT_READ (float): HTTP Read Timeout in Seconds
        HTTP_TIMEOUT_WRITE (float): HTTP Write Timeout in Seconds
        HTTP_TIMEOUT_POOL (float): HTTP Pool Timeout in Seconds
        HTTP2_ENABLED (bool): Enable HTTP/2
        SSL_VERIFY (bool): Verify SSL Certificates

        MONGODB_URI (str): MongoDB URI
        MONGODB_DATABASE (str): MongoDB Database

        MAILER_HOST (str): Mailer Host
        MAILER_PORT (int): Mailer Port
        MAILER_USER (str): Mailer User
        MAILER_PASS (str): Mailer Password
        MAILER_FROM (str): Mailer From
        MAILER_IS_SECURE (bool): Mailer Is Secure
        MAILER_IS_TLS (bool): Mailer Is TLS
        MAILER_IS_SSL (bool): Mailer Is SSL

        ACTIVATION_JWT_SECRET (str): JWT Secret Key
        ACTIVATION_JWT_ALGORITHM (str): JWT Algorithm
        ACTIVATION_JWT_EXPIRE (int): JWT Expiration Time in Seconds

        ACCESS_JWT_SECRET (str): JWT Secret Key
        ACCESS_JWT_ALGORITHM (str): JWT Algorithm
        ACCESS_JWT_EXPIRE (int): JWT Expiration Time in Seconds

        REFRESH_JWT_SECRET (str): JWT Secret Key
        REFRESH_JWT_ALGORITHM (str): JWT Algorithm
        REFRESH_JWT_EXPIRE (int): JWT Expiration Time in Seconds

        DEACTIVATE_JWT_SECRET (str): JWT Secret Key
        DEACTIVATE_JWT_ALGORITHM (str): JWT Algorithm
        DEACTIVATE_JWT_EXPIRE (int): JWT Expiration Time in Seconds

        DELETE_JWT_SECRET (str): JWT Secret Key
        DELETE_JWT_ALGORITHM (str): JWT Algorithm
        DELETE_JWT_EXPIRE (int): JWT Expiration Time in Seconds

        RESET_PASSWORD_JWT_SECRET (str): JWT Secret Key
        RESET_PASSWORD_JWT_ALGORITHM (str): JWT Algorithm
        RESET_PASSWORD_JWT_EXPIRE (int): JWT Expiration Time in Seconds

        SENTRY_DSN (str): Sentry DSN
        SENTRY_SAMPLE_RATE (float): Sentry Sample Rate

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
    PROJECT_DOMAIN: str = "http://localhost:8080"
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

    # OpenTelemetry Configuration
    OTLP_HTTP_ENDPOINT: str = "http://otel-collector-service:4318/v1/traces"
    OTLP_SERVICE_ID: str = "c9fa747e-04ae-4c41-a9a7-5ebd3f706cee"

    # Celery Configuration
    CELERY_BROKER_URL: str = "amqp://NGeDFwAgoZwmMvP:ftT4tT0Qy2cQXGm@rabbitmq-service:5672//"
    CELERY_RESULT_BACKEND: str = "cassandra://"

    # Cassandra Configuration
    CASSANDRA_HOST: str = "cassandra-service"
    CASSANDRA_PORT: int = 9042
    CASSANDRA_USER: str = "cassandra"
    CASSANDRA_PASS: str = "geF4eXLov37FTeg"  # noqa: S105
    CASSANDRA_KEYSPACE: str = "celery_results"

    # Redis Configuration
    REDIS_URL: str = "redis://:WFyzhcO3ByZIjdd@redis-service:6379/"
    REDIS_HOST: str = "redis-service"
    REDIS_PORT: int = 6379
    REDIS_USER: str = ""
    REDIS_PASS: str = "WFyzhcO3ByZIjdd"  # noqa: S105
    REDIS_HTTP_RATE_LIMIT_DB: int = 0
    REDIST_TOKEN_CACHE_DB: int = 1

    # Rate Limit Configuration
    RATE_LIMIT: int = 60
    RATE_LIMIT_WINDOW: int = 60

    # HTTP Connection Pool Settings
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_KEEPALIVE_CONNECTIONS: int = 20
    HTTP_KEEPALIVE_EXPIRY: int = 60  # seconds
    HTTP_TIMEOUT: float = 5.0
    HTTP_TIMEOUT_CONNECT: float = 5.0
    HTTP_TIMEOUT_READ: float = 30.0
    HTTP_TIMEOUT_WRITE: float = 30.0
    HTTP_TIMEOUT_POOL: float = 5.0
    HTTP2_ENABLED: bool = True
    SSL_VERIFY: bool = True

    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://KHOS1bTrd0RBv0b:OOaooAAuAzH5ewb@mongodb-service:27017"
    MONGODB_DATABASE: str = "initstack"

    # Mailer Configuration
    MAILER_HOST: str = "mailpit-service"
    MAILER_PORT: int = 1025
    MAILER_USER: str = ""
    MAILER_PASS: str = ""
    MAILER_FROM: str = "initstack@protonmail.com"
    MAILER_IS_SECURE: bool = False
    MAILER_IS_TLS: bool = False
    MAILER_IS_SSL: bool = False

    # JWT Activation Configuration
    ACTIVATION_JWT_SECRET: str = "7ff220d5c462c4f45d5766aef33333ed4c3ea21e50ebb725450f0c740cdc843e"  # noqa: S105
    ACTIVATION_JWT_ALGORITHM: str = "HS256"
    ACTIVATION_JWT_EXPIRE: int = 1800

    # JWT Access Configuration
    ACCESS_JWT_SECRET: str = "4225d46ff9dfbf537e3053f7899d07def9a12a858c1ca34453b6df1fdb826c64"  # noqa: S105
    ACCESS_JWT_ALGORITHM: str = "HS256"
    ACCESS_JWT_EXPIRE: int = 3600

    # JWT Refresh Configuration
    REFRESH_JWT_SECRET: str = "4e3a2f132c733c87df7f39b2bc55b45f047b358e59c95846e98e9cee6fed5647"  # noqa: S105
    REFRESH_JWT_ALGORITHM: str = "HS256"
    REFRESH_JWT_EXPIRE: int = 86400

    # Deactivate JWT Configuration
    DEACTIVATE_JWT_SECRET: str = "30598412e6fb2d65c811698da21a5fc0776d69f9131ee14303cb4434ffaf186c"  # noqa: S105
    DEACTIVATE_JWT_ALGORITHM: str = "HS256"
    DEACTIVATE_JWT_EXPIRE: int = 86400

    # Delete JWT Configuration
    DELETE_JWT_SECRET: str = "e2be6bed27877f0b74fca944722fde0207d7f5d8d98bed6f025df5bb1bd49ccf"  # noqa: S105
    DELETE_JWT_ALGORITHM: str = "HS256"
    DELETE_JWT_EXPIRE: int = 86400

    # Reset Password JWT Configuration
    RESET_PASSWORD_JWT_SECRET: str = "2738c98c971b6e17637446b83baf5359a76802dbf91b20565c1e1cd65ae507a2"  # noqa: S105
    RESET_PASSWORD_JWT_ALGORITHM: str = "HS256"  # noqa: S105
    RESET_PASSWORD_JWT_EXPIRE: int = 86400

    # Sentry Configuration
    SENTRY_DSN: str = "https://4787ddf812f5e8325f109819dc6ac68a@o4507312074915840.ingest.us.sentry.io/4509722861502464"
    SENTRY_SAMPLE_RATE: float = 1.0

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
