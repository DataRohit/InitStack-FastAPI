# Standard Library Imports
import os

# Third-Party Imports
import uvicorn
from uvicorn.config import LOGGING_CONFIG

# Local Imports
from config.settings import settings

# Disable Uvicorn Access Logs
LOGGING_CONFIG["loggers"]["uvicorn.access"] = {
    "handlers": [],
    "propagate": False,
}

# Keep Error Logs Only
LOGGING_CONFIG["loggers"]["uvicorn.error"] = {
    "level": "INFO",
    "handlers": ["default"],
    "propagate": False,
}


# Main Function
def main() -> None:
    """
    Main Function

    This Function Initializes and Runs the FastAPI Application.
    """

    # Configure Uvicorn
    uvicorn.run(
        "config.http_server:app",
        host=settings.HOST,
        port=settings.PORT,
        log_config=LOGGING_CONFIG,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else os.cpu_count(),
        reload_dirs=["/app"],
    )


# If This File is Run Directly
if __name__ == "__main__":
    # Run the Application
    main()
