"""Base exception classes for Housing & Properties."""

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException


class BaseAPIException(APIException):
    """Base exception class for all custom API exceptions."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An error occurred"
    default_code = "error"

    def __init__(
        self, detail: str | dict[str, Any] | None = None, code: str | None = None
    ):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        super().__init__(detail=detail, code=code)


class ConflictError(BaseAPIException):
    """Exception for conflict errors (409)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Request conflicts with current state."
    default_code = "conflict"


class UnprocessableEntityError(BaseAPIException):
    """Exception for unprocessable entity errors (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Unable to process the request."
    default_code = "unprocessable_entity"
