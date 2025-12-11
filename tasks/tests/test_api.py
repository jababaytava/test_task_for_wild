import pytest
from rest_framework.test import APIClient

from tasks.models import Task, Worker


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_create_task_list_retrieve_and_patch_status_flow(client: APIClient):
    # Create task
    resp = client.post(
        "/api/tasks/",
        {"description": "Do API", "priority": 2},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    tid = resp.data["id"]
    assert resp.data["status"] == Task.Status.PENDING

    # List tasks (paginated)
    resp = client.get("/api/tasks/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert len(resp.data["results"]) == 1

    # Retrieve
    resp = client.get(f"/api/tasks/{tid}/")
    assert resp.status_code == 200
    assert resp.data["priority"] == 2

    # Invalid transition: pending -> completed (skip in_progress)
    resp = client.patch(
        f"/api/tasks/{tid}/",
        {"status": Task.Status.COMPLETED},
        format="json",
    )
    assert resp.status_code == 400

    # Valid transitions pending -> in_progress -> completed
    resp = client.patch(
        f"/api/tasks/{tid}/",
        {"status": Task.Status.IN_PROGRESS},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["status"] == Task.Status.IN_PROGRESS

    resp = client.patch(
        f"/api/tasks/{tid}/",
        {"status": Task.Status.COMPLETED},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["status"] == Task.Status.COMPLETED


@pytest.mark.django_db
def test_worker_create_and_patch_max_concurrent_tasks_only(client: APIClient):
    # Create worker
    resp = client.post(
        "/api/workers/",
        {"name": "WAPI", "max_concurrent_tasks": 2},
        format="json",
    )
    assert resp.status_code == 201
    wid = resp.data["id"]

    # Try to change name via PATCH (should be ignored by serializer) and change capacity
    resp = client.patch(
        f"/api/workers/{wid}/",
        {"name": "NOPE", "max_concurrent_tasks": 3},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["max_concurrent_tasks"] == 3
    assert resp.data["name"] == "WAPI"  # unchanged


@pytest.mark.django_db
def test_stats_endpoints(client: APIClient):
    w1 = Worker.objects.create(name="W1", max_concurrent_tasks=2)
    # Create tasks in different statuses
    Task.objects.create(description="A", priority=1)
    Task.objects.create(
        description="B", priority=2, status=Task.Status.IN_PROGRESS, assignee=w1
    )
    Task.objects.create(
        description="C", priority=3, status=Task.Status.COMPLETED, assignee=w1
    )

    # Summary
    resp = client.get("/api/stats/summary/")
    assert resp.status_code == 200
    body = resp.data
    assert body["total"] == 3
    assert body["per_status"]["pending"] == 1
    assert body["per_status"]["in_progress"] == 1
    assert body["per_status"]["completed"] == 1

    # Workers load
    resp = client.get("/api/stats/workers/")
    assert resp.status_code == 200
    names = [w["name"] for w in resp.data]
    assert "W1" in names
    w1row = next(x for x in resp.data if x["name"] == "W1")
    assert w1row["active_count"] == 1
