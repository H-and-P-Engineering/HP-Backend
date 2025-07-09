from django.utils.deprecation import MiddlewareMixin
from rest_framework.request import Request

from apps.authentication.infrastructure.factory import get_blacklisted_token_repository
from core.infrastructure.logging.base import logger


class TokenBlackListMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.blacklisted_token_repository = get_blacklisted_token_repository()

    def process_request(self, request: Request) -> None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]

            if self.blacklisted_token_repository.exists(access_token):
                request.META["HTTP_AUTHORIZATION"] = ""
                logger.warning(
                    f"Blacklisted token ({access_token[:20]}...) attempted to access {str(request.path)}."
                )

        return None
