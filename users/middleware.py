from collections.abc import Callable

from asgiref.sync import async_to_sync, iscoroutinefunction
from django.utils.decorators import sync_and_async_middleware
from loguru import logger
from rest_framework.request import Request
from rest_framework.response import Response

from core.container import container

AUTH_PATHS = [
    "/api/v1/authentication/login/",
    "/api/v1/authentication/register/",
    "/api/v1/authentication/verify-email/",
    "/api/v1/authentication/request-verification/",
    "/api/v1/authentication/token/refresh/",
]


@sync_and_async_middleware
class TokenBlackListMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)

    def __call__(self, request: Request) -> Response:
        if not self.is_async:
            async_to_sync(self._check_blacklist)(request)
            return self.get_response(request)

        return self.__acall__(request)

    async def __acall__(self, request: Request) -> Response:
        await self._check_blacklist(request)
        return await self.get_response(request)

    async def _check_blacklist(self, request: Request) -> None:
        path = request.path_info if hasattr(request, "path_info") else request.path

        # Clear Authorization header for auth endpoints so expired tokens don't block login
        if any(path.startswith(auth_path) for auth_path in AUTH_PATHS):
            if request.META.get("HTTP_AUTHORIZATION"):
                request.META["HTTP_AUTHORIZATION"] = ""
            return

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
            if await container.blacklisted_token_repository().check_exists(access_token):
                request.META["HTTP_AUTHORIZATION"] = ""
                logger.warning(
                    "Blacklisted token attempted access",
                    token_prefix=access_token[:20],
                    path=str(path),
                )
