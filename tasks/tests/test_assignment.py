import pytest

from tasks.models import Task, Worker
from tasks.services import AssignmentService


@pytest.mark.django_db
def test_assign_respects_capacity_and_least_loaded():
    w1 = Worker.objects.create(name="W1", max_concurrent_tasks=1)
    w2 = Worker.objects.create(name="W2", max_concurrent_tasks=2)
    # 5 pending tasks
    for i in range(5):
        Task.objects.create(description=f"T{i}", priority=2)

    svc = AssignmentService()
    assigned = svc.assign_pending_tasks()

    # Total capacity 3 -> only 3 tasks should be assigned
    assert assigned == 3
    assert Task.objects.filter(status=Task.Status.IN_PROGRESS).count() == 3
    # Load distribution: w1=1, w2=2
    assert Task.objects.filter(status=Task.Status.IN_PROGRESS, assignee=w1).count() == 1
    assert Task.objects.filter(status=Task.Status.IN_PROGRESS, assignee=w2).count() == 2


@pytest.mark.django_db
def test_assignment_picks_highest_priority_first():
    w = Worker.objects.create(name="W", max_concurrent_tasks=1)
    # Create different priorities; expect priority=1 to be picked
    t_high = Task.objects.create(description="high", priority=1)
    t_mid = Task.objects.create(description="mid", priority=3)
    t_low = Task.objects.create(description="low", priority=5)

    svc = AssignmentService()
    assigned = svc.assign_pending_tasks()

    assert assigned == 1
    t_high.refresh_from_db()
    assert t_high.status == Task.Status.IN_PROGRESS
    assert Task.objects.filter(status=Task.Status.PENDING).count() == 2


@pytest.mark.django_db
def test_autoscale_adds_worker_when_pending_gt_10():
    # 11 pending tasks, no workers
    for i in range(11):
        Task.objects.create(description=f"T{i}", priority=2)

    svc = AssignmentService()
    added, deactivated = svc.autoscale_workers()

    assert added == 1
    assert deactivated == 0
    assert Worker.objects.filter(is_active=True).count() == 1


@pytest.mark.django_db
def test_autoscale_deactivates_to_two_when_pending_lt_5():
    # Create 4 active workers
    for i in range(4):
        Worker.objects.create(name=f"W{i}", max_concurrent_tasks=1, is_active=True)

    # No pending tasks
    svc = AssignmentService()
    added, deactivated = svc.autoscale_workers()

    assert added == 0
    assert deactivated == 2
    assert Worker.objects.filter(is_active=True).count() == 2
