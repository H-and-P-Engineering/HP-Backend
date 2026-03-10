import logging
import re
import sys
from functools import lru_cache
from typing import Any

from loguru import logger


SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "key",
    "auth",
    "credential",
    "api",
    "session",
    "state",
    "scope",
    "cookie",
    "email",
    "link",
    "address",
    "phone",
    "mobile",
    "verification",
    "code",
    "signature",
    "jwt",
    "phone_number",
}

SENSITIVE_PATTERN = re.compile(
    rf'(?i)({"|".join(SENSITIVE_KEYS)})(["\']?\s*[:=]\s*["\']?)([^"\'\s,&{{}}]+)(["\']?)'
)

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

JWT_PATTERN = re.compile(r"ey[a-zA-Z0-9\-_]+\.ey[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+")

CONNECTION_URL_PATTERN = re.compile(r"(?i)([a-z0-9+]+://)(?:[^@\s]+@)?([^ \n\r\t,]+)")

URL_SENSITIVE_PATTERN = re.compile(
    r"(?i)([\?&](?:token|code|state|access_token|refresh_token|secret|password|key|api)=)([^&\s#]+)"
)


def sanitize_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: sanitize_data(v)
            if not any(s in k.lower() for s in SENSITIVE_KEYS)
            else "********"
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [sanitize_data(item) for item in data]
    if isinstance(data, str):
        data = SENSITIVE_PATTERN.sub(r"\1\2********\4", data)
        data = CONNECTION_URL_PATTERN.sub(r"\1********", data)
        data = URL_SENSITIVE_PATTERN.sub(r"\1********", data)
        data = EMAIL_PATTERN.sub("********", data)
        data = JWT_PATTERN.sub("********", data)
        return data

    # Handle non-serializable objects (like Coroutines, UUIDs, etc.)
    if not isinstance(data, (dict, list, tuple, str, int, float, bool, type(None))):
        return str(data)

    return data


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(
            logger_name=record.name
        ).log(level, record.getMessage())


@lru_cache(maxsize=1)
def setup_logging(log_level: str, log_file: str):
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level)

    for file in logging.root.manager.loggerDict.keys():
        logging.getLogger(file).handlers = []
        logging.getLogger(file).propagate = True

    def should_log(record):
        return record["extra"].get("target") != "file"

    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <5}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "filter": should_log,
                "backtrace": True,
                "diagnose": False,
            },
            {
                "sink": log_file,
                "rotation": "10 MB",
                "retention": "10 days",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <5} | {file}:{line} - {message}",
                "filter": should_log,
                "backtrace": True,
                "diagnose": False,
            },
        ],
        patcher=lambda record: record.update(
            extra=sanitize_data(record["extra"]),
            message=sanitize_data(record["message"]),
        ),
    )
