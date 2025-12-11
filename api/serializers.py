from rest_framework import serializers

from tasks.models import Task, Worker


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = [
            "id",
            "name",
            "max_concurrent_tasks",
            "is_active",
        ]
        read_only_fields = ["is_active"]


class WorkerUpdateCapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ["max_concurrent_tasks"]


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source="assignee.name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "description",
            "priority",
            "status",
            "created_at",
            "completed_at",
            "assignee",
            "assignee_name",
        ]
        read_only_fields = ["created_at", "completed_at"]


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["status"]

    def validate_status(self, value: str) -> str:
        instance: Task = self.instance
        if not instance:
            return value
        current = instance.status
        if current == Task.Status.PENDING and value == Task.Status.IN_PROGRESS:
            return value
        if current == Task.Status.IN_PROGRESS and value == Task.Status.COMPLETED:
            return value
        if value == current:
            return value
        raise serializers.ValidationError(
            "Invalid status transition. Allowed: pending→in_progress, in_progress→completed."
        )
