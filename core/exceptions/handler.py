"""Custom exception handlers for the Housing & Properties API."""

from typing import Any

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.logging.base import logger

from .base import ConflictError, UnprocessableEntityError


def normalize_error_detail(detail: Any) -> str | list[str] | dict[str, Any]:
    """Normalize error details to a consistent format."""

    if isinstance(detail, str):
        return detail

    if isinstance(detail, dict):
        normalized = {}
        for key, value in detail.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                if len(value) == 1 and hasattr(value[0], "message"):
                    normalized[key] = str(value[0].message)
                else:
                    values_list = list(value)
                    normalized[key] = (
                        str(values_list[0])
                        if len(values_list) == 1
                        else [
                            str(v.message) if hasattr(v, "message") else str(v)
                            for v in values_list
                        ]
                    )
            else:
                normalized[key] = str(value)
        return normalized

    if hasattr(detail, "__iter__"):
        return [str(item) for item in detail]

    return str(detail)


def hp_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler for DRF that provides consistent error responses.

    Args:
        exc: The exception instance
        context: Additional context about the exception

    Returns:
        Response object with formatted error data or None
    """

    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(
            detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )
    elif isinstance(exc, IntegrityError):
        exc = ConflictError(
            detail=f"Database constraint violation occurred: {str(exc)}"
        )
    elif isinstance(exc, exceptions.ParseError):
        exc = UnprocessableEntityError(detail=str(exc.detail))

    response = exception_handler(exc, context)

    custom_response_data = {
        "success": False,
        "message": "An error occurred",
        "errors": {},
        "status_code": None,
    }

    if response is None:
        import traceback

        tb = traceback.extract_tb(exc.__traceback__)
        if tb:
            last_frame = tb[-1]
            location = f'File "{last_frame.filename}", line {last_frame.lineno}, in {last_frame.name}\n    {last_frame.line}'  # noqa
        else:
            location = "No traceback available"

        exc_type = type(exc).__name__
        exc_msg = str(exc)
        logger.error(
            f"Unhandled exception in hp_exception_handler -> {exc_type}: {exc_msg}\n{location}"  # noqa
        )

        custom_response_data["errors"] = {"detail": "Internal server error"}
        custom_response_data["status_code"] = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(
            data=custom_response_data,
            status=custom_response_data["status_code"],
        )

    custom_response_data["status_code"] = response.status_code

    # Handle specific exceptions
    if isinstance(exc, Http404):
        custom_response_data["message"] = "Resource not found"
        custom_response_data["errors"] = {"detail": str(exc)}
    elif isinstance(exc, PermissionDenied):
        custom_response_data["message"] = "Permission denied"
        custom_response_data["errors"] = {"detail": str(exc.detail)}
    elif isinstance(exc, exceptions.ValidationError):
        custom_response_data["message"] = "Validation error"
        custom_response_data["errors"] = {
            "detail": normalize_error_detail(response.data)
        }
    elif isinstance(exc, exceptions.AuthenticationFailed):
        custom_response_data["message"] = "Authentication failed"
        custom_response_data["errors"] = {"detail": str(exc.detail)}
    elif isinstance(exc, exceptions.NotAuthenticated):
        custom_response_data["message"] = "Authentication required"
        custom_response_data["errors"] = {"detail": str(exc)}
    elif isinstance(exc, exceptions.MethodNotAllowed):
        custom_response_data["message"] = "Method not allowed"
        custom_response_data["errors"] = {"detail": str(exc)}
    elif isinstance(exc, exceptions.NotFound):
        custom_response_data["message"] = "Not found"
        custom_response_data["errors"] = {"detail": str(exc.detail)}
    elif isinstance(exc, exceptions.Throttled):
        custom_response_data["message"] = "Rate limit exceeded"
        custom_response_data["errors"] = {
            "detail": f"Rate limit exceeded. Try again in {exc.wait} seconds."
        }
    else:
        # Generic error handling
        if hasattr(exc, "detail"):
            custom_response_data["errors"] = {"detail": str(exc.detail)}
        else:
            custom_response_data["errors"] = {"detail": "An error occurred."}

    response.data = custom_response_data

    return response
