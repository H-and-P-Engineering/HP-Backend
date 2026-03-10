from collections.abc import Sequence
from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .base import BaseTask


@shared_task(base=BaseTask, queue="emails")
def send_email_task(
    subject: str,
    template_name: str,
    context: dict[str, Any],
    recipient_list: Sequence[str],
    from_email: str | None = None,
) -> int:
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string(f"{template_name}.html", context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list,
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()
