from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Worker(models.Model):
    name = models.CharField(max_length=150, unique=True)
    max_concurrent_tasks = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"], name="worker_active_idx"),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    description = models.TextField()
    priority = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 = highest priority, 5 = lowest",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(
        Worker,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tasks",
    )

    class Meta:
        indexes = [
            models.Index(fields=["priority"], name="task_priority_idx"),
            models.Index(fields=["assignee"], name="task_assignee_idx"),
        ]
        ordering = ["priority", "created_at"]

    def __str__(self) -> str:
        return f"Task#{self.pk} (p{self.priority}) - {self.get_status_display()}"
