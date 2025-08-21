from typing import Any

from django.contrib.auth import REDIRECT_FIELD_NAME
from social_core.actions import do_auth
from social_core.utils import partial_pipeline_data


def begin_social_auth(request: Any, user_type: str) -> Any:
    return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)
