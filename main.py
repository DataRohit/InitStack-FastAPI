import uvicorn

from config.settings import settings


def main():
    """Run InitStack FastAPI Development Server.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    uvicorn.run(
        app="config.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True,
    )


if __name__ == "__main__":
    main()
