import contextvars
import json
import logging
import re
import sys
from pathlib import Path
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


request_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "request_context", default=None
)


class LogFormat:
    _LEVEL_COLOURS: dict[str, str] = {
        "CRITICAL": "red",
        "ERROR": "magenta",
        "WARNING": "yellow",
        "SUCCESS": "green",
        "INFO": "blue",
        "DEBUG": "white",
        "TRACE": "dim",
    }

    def __init__(self, record: Any) -> None:
        self._record = record
        self.time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.level = record["level"].name
        self._colour = self._LEVEL_COLOURS.get(self.level, "white")

        # Loguru exposes function name as "<module>" for top-level code;
        # angle brackets must be escaped so Loguru doesn't treat them as markup.
        func = record["function"]
        self.location = (
            f"{record['file'].name}:"
            f"{'<module>' if func == '<module>' else func}:"
            f"{record['line']}"
        )

    def console(self) -> str:
        colour = self._colour
        return (
            f"<dim><bold>{self.time_str}</bold></dim> | "
            f"<{colour}>{self.level:<8}</{colour}> | "
            f"<cyan>{self.location}</cyan> - "
            f"<{colour}>{self._record['message']}</{colour}>"
            "\n"
        )

    def file(self) -> str:
        extras = {
            key: value
            for key, value in self._record["extra"].items()
            if key != "request_id" and value is not None
        }

        context_parts = []

        for key, value in extras.items():
            if isinstance(value, dict | list | tuple):
                safe_value = json.dumps(value, default=str)
            else:
                safe_value = str(value)

            # Escape braces so Loguru doesn't treat them as format placeholders
            safe_value = safe_value.replace("{", "{{").replace("}", "}}")
            context_parts.append(f"{key}={safe_value}")

        context_str = f" | {', '.join(context_parts)}" if context_parts else ""

        request_id = self._record["extra"].get("request_id", "")
        rid_str = f" | rid={request_id}" if request_id else ""

        return (
            f"{self.time_str} | "
            f"{self.level:<8} | "
            f"{self.location}"
            f"{rid_str}"
            f" - {self._record['message']}"
            f"{context_str}"
            "\n"
        )


_LOGGING_FILE = logging.__file__.rstrip("c")  # strip trailing 'c' from .pyc if present


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: logging.FrameType | None = sys._getframe(1)  # type: ignore[assignment]
        depth = 1
        while frame:
            # Normalise .pyc → .py so the comparison works across all Python/macOS combos
            filename = frame.f_code.co_filename.rstrip("c")
            if filename != _LOGGING_FILE:
                break
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        ctx = request_context.get() or {}
        (
            logger.opt(depth=depth, exception=record.exc_info)
            .bind(**ctx)
            .log(level, record.getMessage())
        )


def _context_patcher(record: Any) -> None:  # type: ignore[type-arg]
    ctx = request_context.get()
    if ctx:
        record["extra"].update(ctx)

    record["message"] = sanitize_data(record["message"])


def setup_logging(
    log_level: str, log_file: Path = Path("logs/app.log"), environment: str = "local"
) -> None:
    is_local = environment.lower() in {"local", "dev", "development"}

    logger.remove()

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logging.root.setLevel(log_level)

    for name in list(logging.root.manager.loggerDict):
        lib_logger = logging.getLogger(name)
        lib_logger.handlers = []
        lib_logger.propagate = True

    # Suppress Django's dev-server access log lines ("GET /... 200") — these
    # are equivalent to uvicorn.access and add noise without useful context.
    # django.request (error-level 500s) still propagates via the root logger.
    logging.getLogger("django.server").propagate = False

    log_file.parent.mkdir(parents=True, exist_ok=True)
    error_log_file = log_file.with_name(log_file.stem + "_errors" + log_file.suffix)

    # Sink 1: stdout (coloured in local, JSON in production)
    logger.add(
        sys.stdout,
        level=log_level,
        colorize=is_local,
        serialize=not is_local,  # JSON lines in staging/production
        backtrace=False,
        diagnose=is_local,  # full variable introspection locally only
        format=lambda rec: LogFormat(rec).console(),
    )

    # Sink 2: rotating info+ file (always JSON for structured ingestion)
    logger.add(
        str(log_file),
        level="INFO",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,  # thread/async-safe writes
        backtrace=True,
        diagnose=False,  # never dump locals to disk (secrets)
        serialize=True,
        format=lambda rec: LogFormat(rec).file(),
    )

    # Sink 3: error-only file (long retention for post-mortems)
    logger.add(
        str(error_log_file),
        level="ERROR",
        rotation="10 MB",
        retention="60 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        serialize=True,
        format=lambda rec: LogFormat(rec).file(),
    )

    logger.configure(patcher=_context_patcher)

    logger.info(
        "Logging configured | level={} env={} file={}",
        log_level,
        environment,
        log_file,
    )
