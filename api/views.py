from typing import Any, Dict, List

from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from tasks.models import Task, Worker
from tasks.services import AssignmentService
from .serializers import (
    TaskSerializer,
    TaskStatusUpdateSerializer,
    WorkerSerializer,
    WorkerUpdateCapacitySerializer,
)


class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Task.objects.select_related("assignee").all().order_by("-id")
    serializer_class = TaskSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action in {"partial_update"}:
            return TaskStatusUpdateSerializer
        return super().get_serializer_class()

    @extend_schema(
        request=TaskStatusUpdateSerializer,
        responses={200: TaskSerializer},
        description="Partial update of task status: allowed transitions pending→in_progress→completed",
    )
    def partial_update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        full = TaskSerializer(instance=self.get_object())
        return Response(full.data)


class WorkerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Worker.objects.all().order_by("name")
    serializer_class = WorkerSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action in {"partial_update"}:
            return WorkerUpdateCapacitySerializer
        return super().get_serializer_class()

    @extend_schema(
        request=WorkerUpdateCapacitySerializer,
        responses={200: WorkerSerializer},
        description="Partial update of worker: only max_concurrent_tasks is allowed",
    )
    def partial_update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        full = WorkerSerializer(instance=self.get_object())
        return Response(full.data)


class StatsSummaryView(APIView):

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "per_status": {
                        "type": "object",
                        "properties": {
                            "pending": {"type": "integer"},
                            "in_progress": {"type": "integer"},
                            "completed": {"type": "integer"},
                        },
                    },
                },
            }
        },
        description="Aggregated tasks statistics by status",
    )
    @method_decorator(cache_page(5))
    def get(self, request):
        total = Task.objects.count()
        per_status = {
            Task.Status.PENDING: Task.objects.filter(
                status=Task.Status.PENDING
            ).count(),
            Task.Status.IN_PROGRESS: Task.objects.filter(
                status=Task.Status.IN_PROGRESS
            ).count(),
            Task.Status.COMPLETED: Task.objects.filter(
                status=Task.Status.COMPLETED
            ).count(),
        }
        return Response(
            {
                "total": total,
                "per_status": {
                    "pending": per_status[Task.Status.PENDING],
                    "in_progress": per_status[Task.Status.IN_PROGRESS],
                    "completed": per_status[Task.Status.COMPLETED],
                },
            }
        )


class StatsWorkersView(APIView):
    @extend_schema(
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "is_active": {"type": "boolean"},
                        "max_concurrent_tasks": {"type": "integer"},
                        "active_count": {"type": "integer"},
                    },
                },
            }
        },
        description="Workers with current active (in_progress) tasks count",
    )
    @method_decorator(cache_page(5))
    def get(self, request):
        svc = AssignmentService()
        loads = svc.get_active_workers_with_load()
        inactive = (
            Worker.objects.filter(is_active=False)
            .annotate(
                active_count=Count(
                    "tasks",
                    filter=Q(tasks__status=Task.Status.IN_PROGRESS),
                )
            )
            .order_by("name")
        )
        data: List[Dict[str, Any]] = []
        for wl in loads:
            w = wl.worker
            data.append(
                {
                    "id": w.id,
                    "name": w.name,
                    "is_active": w.is_active,
                    "max_concurrent_tasks": w.max_concurrent_tasks,
                    "active_count": wl.active_count,
                }
            )
        for w in inactive:
            data.append(
                {
                    "id": w.id,
                    "name": w.name,
                    "is_active": w.is_active,
                    "max_concurrent_tasks": w.max_concurrent_tasks,
                    "active_count": w.active_count or 0,
                }
            )
        return Response(data)
