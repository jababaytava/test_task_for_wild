import pytest
from django.test import override_settings

from tasks.models import Task, Worker
from tasks.services import AssignmentService


@pytest.mark.django_db
@override_settings(ASSIGNMENT_MAX_PER_RUN=5)
def test_assignment_respects_max_per_run_limit_when_capacity_is_higher():
    # One worker with capacity 10 (higher than limit)
    w = Worker.objects.create(name="WCap10", max_concurrent_tasks=10)
    for i in range(50):
        Task.objects.create(description=f"T{i}", priority=2)

    svc = AssignmentService()
    assigned = svc.assign_pending_tasks()

    # Limit is 5, capacity is 10 => should assign 5
    assert assigned == 5
    assert Task.objects.filter(status=Task.Status.IN_PROGRESS, assignee=w).count() == 5


@pytest.mark.django_db
@override_settings(ASSIGNMENT_MAX_PER_RUN=20)
def test_assignment_respects_capacity_when_less_than_limit():
    # Total capacity = 3; limit is 20
    w1 = Worker.objects.create(name="W1", max_concurrent_tasks=1)
    w2 = Worker.objects.create(name="W2", max_concurrent_tasks=2)
    for i in range(50):
        Task.objects.create(description=f"T{i}", priority=2)

    svc = AssignmentService()
    assigned = svc.assign_pending_tasks()

    # Capacity is 3 -> should assign only 3
    assert assigned == 3
    assert Task.objects.filter(status=Task.Status.IN_PROGRESS).count() == 3
