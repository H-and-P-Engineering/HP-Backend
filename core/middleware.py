import time
import uuid
from collections.abc import Callable

from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import sync_and_async_middleware
from loguru import logger

from core.logging import request_context, sanitize_data


def _client_ip(request: HttpRequest) -> str:
    """Return the real client IP, honouring proxy headers."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.META.get("HTTP_X_REAL_IP")
    if real_ip:
        return real_ip.strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _build_context(request: HttpRequest, request_id: str) -> dict:
    """Build the log context dict for a request."""
    path = request.path
    method = request.method or "UNKNOWN"
    client_ip = _client_ip(request)
    user_agent = (request.META.get("HTTP_USER_AGENT", "") or "")[:200]

    ctx: dict = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "client_ip": client_ip,
    }
    if user_agent:
        ctx["user_agent"] = user_agent

    # Sanitize and attach query string if present
    query = request.META.get("QUERY_STRING", "")
    if query:
        ctx["query"] = sanitize_data(query)

    return ctx


# Paths whose successful responses we don't want to log at INFO (health/static noise)
_SILENT_PATHS = {"/", "/health/", "/favicon.ico"}


@sync_and_async_middleware
class RequestLoggingMiddleware:
    """Attach a unique request_id and request metadata to the Loguru context.

    All log calls made during the request automatically carry these fields.
    Mirrors social-badge-api's RequestLoggingMiddleware, adapted for Django's
    sync_and_async_middleware pattern.
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)

    # ------------------------------------------------------------------ sync

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if self.is_async:
            return self.__acall__(request)  # type: ignore[return-value]

        request_id = uuid.uuid4().hex
        ctx = _build_context(request, request_id)
        token = request_context.set(ctx)

        is_silent = request.path in _SILENT_PATHS
        if not is_silent:
            logger.info("→ {} {}", ctx["method"], ctx["path"])

        start = time.perf_counter()
        try:
            response: HttpResponse = self.get_response(request)
        except Exception:
            logger.error(
                "✗ {} {} — unhandled exception after {:.1f}ms",
                ctx["method"],
                ctx["path"],
                (time.perf_counter() - start) * 1000,
            )
            raise
        finally:
            request_context.reset(token)

        elapsed = (time.perf_counter() - start) * 1000
        status = response.status_code
        level = "WARNING" if status >= 400 else "INFO"

        if not is_silent or status >= 400:
            logger.log(
                level,
                "← {} {} {} {:.1f}ms",
                ctx["method"],
                ctx["path"],
                status,
                elapsed,
            )

        return response

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        request_id = uuid.uuid4().hex
        ctx = _build_context(request, request_id)
        token = request_context.set(ctx)

        is_silent = request.path in _SILENT_PATHS
        if not is_silent:
            logger.info("→ {} {}", ctx["method"], ctx["path"])

        start = time.perf_counter()
        try:
            response: HttpResponse = await self.get_response(request)
        except Exception:
            logger.error(
                "✗ {} {} — unhandled exception after {:.1f}ms",
                ctx["method"],
                ctx["path"],
                (time.perf_counter() - start) * 1000,
            )
            raise
        finally:
            request_context.reset(token)

        elapsed = (time.perf_counter() - start) * 1000
        status = response.status_code
        level = "WARNING" if status >= 400 else "INFO"

        if not is_silent or status >= 400:
            logger.log(
                level,
                "← {} {} {} {:.1f}ms",
                ctx["method"],
                ctx["path"],
                status,
                elapsed,
            )

        return response
