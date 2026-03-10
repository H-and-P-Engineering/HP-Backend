from django.db import models
from django.utils.translation import gettext_lazy as _


class FailedTask(models.Model):
    task_id = models.UUIDField(unique=True, verbose_name=_("Task ID"))
    task_name = models.CharField(max_length=255, verbose_name=_("Task Name"))
    args = models.TextField(blank=True, verbose_name=_("Arguments"))
    kwargs = models.TextField(blank=True, verbose_name=_("Keyword Arguments"))
    exception = models.TextField(verbose_name=_("Exception"))
    traceback = models.TextField(blank=True, verbose_name=_("Traceback"))
    queue = models.CharField(max_length=100, blank=True, verbose_name=_("Queue"))
    failed_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Failed At"))
    retried_at = models.DateTimeField(auto_now=True, verbose_name=_("Retried At"))

    class Meta:
        verbose_name = _("Failed Task")
        verbose_name_plural = _("Failed Tasks")
        ordering = ["-failed_at"]

    def __str__(self) -> str:
        return f"{self.task_name} ({self.task_id})"
