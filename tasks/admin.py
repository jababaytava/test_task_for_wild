from django.contrib import admin

from .models import Task, Worker


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("name", "max_concurrent_tasks", "is_active", "active_tasks_count")
    list_filter = ("is_active",)
    search_fields = ("name",)

    @admin.display(description="Active tasks")
    def active_tasks_count(self, obj: Worker) -> int:
        return obj.tasks.filter(status=Task.Status.IN_PROGRESS).count()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "priority",
        "status",
        "assignee",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "priority", "assignee")
    search_fields = ("description",)
    autocomplete_fields = ("assignee",)
    date_hierarchy = "created_at"
