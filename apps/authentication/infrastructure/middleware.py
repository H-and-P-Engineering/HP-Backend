from django.utils.deprecation import MiddlewareMixin
from rest_framework.request import Request

from apps.authentication.infrastructure.models import BlackListedToken
from core.infrastructure.logging.base import logger


class TokenBlackListMiddleware(MiddlewareMixin):
    def process_request(self, request: Request) -> None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]

            if BlackListedToken.is_blacklisted(access_token):
                request.META["HTTP_AUTHORIZATION"] = ""
                logger.warning(
                    f"Blacklisted token ({access_token[:20]}...) attempted to access {str(request.path)}."
                )

        return None
