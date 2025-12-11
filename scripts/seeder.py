import os
import sys


def strtobool(val: str) -> bool:
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    seed_on_start = strtobool(os.getenv("SEED_ON_START", "1"))
    seed_workers = int(os.getenv("SEED_WORKERS", "3") or 0)
    seed_tasks = int(os.getenv("SEED_TASKS", "50") or 0)
    seed_flush = strtobool(os.getenv("SEED_FLUSH", "0"))

    if not seed_on_start:
        print("[seeder] SEED_ON_START is disabled; skipping seeding.")
        return 0
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DRFTaskBalancerTestTask.settings")
    try:
        import django

        django.setup()
    except Exception as exc:
        print(f"[seeder] Failed to setup Django: {exc}")
        return 1

    from django.core.management import call_command
    from tasks.models import Task, Worker

    existing_workers = Worker.objects.count()
    existing_tasks = Task.objects.count()
    if not seed_flush and (existing_workers > 0 or existing_tasks > 0):
        print(
            f"[seeder] Data already present (workers={existing_workers}, tasks={existing_tasks}); skipping seeding."
        )
        return 0

    print(
        f"[seeder] Seeding demo data (workers={seed_workers}, tasks={seed_tasks}, flush={seed_flush})..."
    )
    try:
        args = {
            "workers": max(0, seed_workers),
            "tasks": max(0, seed_tasks),
        }
        if seed_flush:
            # pass the --flush flag
            call_command("seed_demo", **args, flush=True)
        else:
            call_command("seed_demo", **args)
    except SystemExit as se:  # call_command may raise SystemExit for management errors
        print(f"[seeder] Seeding failed with SystemExit: {se}")
        return int(getattr(se, "code", 1) or 1)
    except Exception as exc:
        print(f"[seeder] Seeding failed: {exc}")
        return 1

    print(
        f"[seeder] Seeding completed. Now workers={Worker.objects.count()}, tasks={Task.objects.count()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
