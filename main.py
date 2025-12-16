from typing import TYPE_CHECKING

import uvicorn

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging


def main():
    """Run InitStack FastAPI Development Server.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    logger: logging.Logger = get_logger(name="main")

    logger.info(msg="Starting InitStack FastAPI server")
    logger.info(msg=f"Server configuration: {settings.host}:{settings.port}")
    logger.info(msg=f"Environment: {settings.environment}")
    logger.info(msg=f"Debug mode: {settings.debug}")
    logger.info(msg=f"Reload: {settings.reload}")
    logger.info(msg=f"Workers: {settings.workers if not settings.reload else 1}")

    uvicorn.run(
        app="config.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level="critical",
        access_log=False,
        use_colors=False,
        log_config=None,
    )


if __name__ == "__main__":
    main()
