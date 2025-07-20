# Third-Party Imports
import uvicorn

# Local Imports
from config.settings import settings


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
        reload=settings.RELOAD,
        log_level="info" if settings.DEBUG else "warning",
    )


# If This File is Run Directly
if __name__ == "__main__":
    # Run the Application
    main()
