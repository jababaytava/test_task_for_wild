import pytest
from django.core.exceptions import ValidationError

from tasks.models import Task, Worker


@pytest.mark.django_db
def test_worker_creation_defaults():
    w = Worker.objects.create(name="W1", max_concurrent_tasks=2)
    assert w.is_active is True
    assert w.max_concurrent_tasks == 2


@pytest.mark.django_db
def test_task_defaults_and_status_choices():
    t = Task.objects.create(description="Do it", priority=2)
    assert t.status == Task.Status.PENDING
    assert t.assignee is None


@pytest.mark.django_db
def test_priority_validation():
    w = Worker.objects.create(name="W2", max_concurrent_tasks=1)
    t = Task(description="Invalid priority", priority=0, assignee=w)
    with pytest.raises(ValidationError):
        t.full_clean()


@pytest.mark.django_db
def test_filter_by_status_and_assignee():
    w1 = Worker.objects.create(name="W1", max_concurrent_tasks=1)
    w2 = Worker.objects.create(name="W2", max_concurrent_tasks=1)
    Task.objects.create(description="A", priority=1, assignee=w1)
    Task.objects.create(
        description="B", priority=3, assignee=w1, status=Task.Status.IN_PROGRESS
    )
    Task.objects.create(
        description="C", priority=2, assignee=w2, status=Task.Status.COMPLETED
    )

    assert Task.objects.filter(status=Task.Status.PENDING).count() == 1
    assert Task.objects.filter(status=Task.Status.IN_PROGRESS, assignee=w1).count() == 1
    assert Task.objects.filter(assignee=w2, status=Task.Status.COMPLETED).count() == 1
