import logging
from functools import lru_cache

from django.conf import settings
from loguru import logger


class InterceptHandler(logging.Handler):
    """
    A handler that bridges Python's standard logging to Loguru.

    Key functions:
    - Maps standard log levels to Loguru levels
    - Maintains call stack depth for accurate source tracking
    - Preserves original log context and messages
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


@lru_cache(maxsize=1)
def setup_logging() -> None:
    """
    Configure logging with Loguru.

    This sets logging to stdout and file with proper formatting and rotation.
    """

    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOGGING_LEVEL)

    for file in logging.root.manager.loggerDict.keys():
        logging.getLogger(file).handlers = []
        logging.getLogger(file).propagate = True

    logger.configure(
        handlers=[
            # File output
            {
                "sink": settings.LOG_FILE,
                "rotation": "10 MB",
                "retention": "10 days",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <5} | {file}:{line} - {message}",  # noqa
            },
        ]
    )


setup_logging()
