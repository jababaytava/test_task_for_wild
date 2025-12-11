from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from django.db import transaction
from django.db.models import Count, F, Q
from django.conf import settings

from .models import Task, Worker


@dataclass
class WorkerLoad:
    worker: Worker
    active_count: int


class AssignmentService:

    def get_active_workers_with_load(self) -> List[WorkerLoad]:
        active_qs = (
            Worker.objects.filter(is_active=True)
            .annotate(
                active_count=Count(
                    "tasks",
                    filter=Q(tasks__status=Task.Status.IN_PROGRESS),
                )
            )
            .order_by("active_count", "name")
        )
        return [
            WorkerLoad(worker=w, active_count=w.active_count or 0) for w in active_qs
        ]

    def _choose_worker(self) -> Optional[WorkerLoad]:
        for wl in self.get_active_workers_with_load():
            if wl.active_count < wl.worker.max_concurrent_tasks:
                return wl
        return None

    def assign_pending_tasks(self) -> int:
        assigned = 0
        limit = getattr(settings, "ASSIGNMENT_MAX_PER_RUN", 100)
        pending_qs = Task.objects.filter(status=Task.Status.PENDING).order_by(
            "priority", "created_at", "id"
        )

        for task in pending_qs.iterator():
            chosen = self._choose_worker()
            if not chosen:
                break

            with transaction.atomic():
                current_active = (
                    Task.objects.select_for_update()
                    .filter(status=Task.Status.IN_PROGRESS, assignee=chosen.worker)
                    .count()
                )
                if current_active >= chosen.worker.max_concurrent_tasks:
                    continue

                t = Task.objects.select_for_update().get(pk=task.pk)
                if t.status != Task.Status.PENDING:
                    continue

                t.assignee = chosen.worker
                t.status = Task.Status.IN_PROGRESS
                t.save(update_fields=["assignee", "status"])
                assigned += 1

            if assigned >= max(1, int(limit)):
                break

        return assigned

    def autoscale_workers(self) -> Tuple[int, int]:
        pending = Task.objects.filter(status=Task.Status.PENDING).count()
        added = 0
        deactivated = 0

        if pending > 10:
            base = "Worker-"
            n = 1
            while True:
                name = f"{base}{n:03d}"
                if not Worker.objects.filter(name=name).exists():
                    Worker.objects.create(
                        name=name, max_concurrent_tasks=1, is_active=True
                    )
                    added = 1
                    break
                n += 1

        if pending < 5:
            active = self.get_active_workers_with_load()
            if len(active) > 2:
                extras = active[2:]
                for wl in extras:
                    w = wl.worker
                    w.is_active = False
                    w.save(update_fields=["is_active"])
                    deactivated += 1

        return added, deactivated
