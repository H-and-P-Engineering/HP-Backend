import json

from celery import current_app
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from .models import FailedTask
from .tasks import redrive_all_from_dlq


@admin.register(FailedTask)
class FailedTaskAdmin(admin.ModelAdmin):
    change_list_template = "admin/monitoring/failedtask/change_list.html"

    list_display = (
        "task_name",
        "task_id",
        "queue",
        "failed_at",
        "retried_at",
    )
    list_filter = ("queue", "task_name")
    search_fields = ("task_id", "task_name", "exception")
    readonly_fields = (
        "task_id",
        "task_name",
        "args",
        "kwargs",
        "exception",
        "traceback",
        "queue",
        "failed_at",
        "retried_at",
    )
    actions = ["redrive_selected_tasks"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "redrive-all-from-dlq/",
                self.admin_site.admin_view(self.redrive_all_from_dlq_view),
                name="monitoring_failedtask_redrive_all_from_dlq",
            ),
        ]
        return custom_urls + urls

    def redrive_all_from_dlq_view(self, request):
        if request.method != "POST":
            return HttpResponseRedirect(
                reverse("admin:monitoring_failedtask_changelist")
            )

        try:
            redrive_all_from_dlq.delay()

            self.message_user(
                request,
                _("Bulk redrive started in the background."),
                messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(
                request,
                _(f"Failed to start bulk redrive: {str(e)}"),
                messages.ERROR,
            )

        return HttpResponseRedirect(reverse("admin:monitoring_failedtask_changelist"))

    @admin.action(description=_("Redrive selected tasks (Selective)"))
    def redrive_selected_tasks(self, request, queryset):
        success_count = 0
        for task_record in queryset:
            try:
                args = json.loads(task_record.args) if task_record.args else []
                kwargs = json.loads(task_record.kwargs) if task_record.kwargs else {}

                current_app.send_task(
                    task_record.task_name,
                    args=args,
                    kwargs=kwargs,
                    queue=task_record.queue or "default",
                )

                task_record.delete()
                success_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    _(f"Failed to redrive task {task_record.task_id}: {str(e)}"),
                    messages.ERROR,
                )

        if success_count:
            self.message_user(
                request,
                _(f"Successfully redriven {success_count} tasks."),
                messages.SUCCESS,
            )
