import random
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from tasks.models import Task, Worker


class Command(BaseCommand):
    help = "Seed demo Workers and Tasks for testing/development."

    def add_arguments(self, parser: CommandParser) -> None:  # noqa: D401
        parser.add_argument(
            "--workers",
            type=int,
            default=3,
            help="Number of workers to create (default: 3)",
        )
        parser.add_argument(
            "--tasks",
            type=int,
            default=50,
            help="Number of tasks to create (default: 50)",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing Workers/Tasks before seeding",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        workers_count: int = max(0, int(options.get("workers", 3) or 0))
        tasks_count: int = max(0, int(options.get("tasks", 50) or 0))
        do_flush: bool = bool(options.get("flush", False))

        if do_flush:
            self.stdout.write(self.style.WARNING("Flushing existing data..."))
            Task.objects.all().delete()
            Worker.objects.all().delete()

        # If not flushing and there is already data, be idempotent and exit
        if not do_flush and (Worker.objects.exists() or Task.objects.exists()):
            self.stdout.write(
                self.style.NOTICE(
                    "Data already present; skipping seeding (use --flush to reseed)."
                )
            )
            return None

        self.stdout.write(
            f"Seeding demo data: workers={workers_count}, tasks={tasks_count}"
        )

        # Create workers
        workers: list[Worker] = []
        for i in range(1, workers_count + 1):
            name = f"Worker {i}"
            # Distribute max_concurrent_tasks between 1 and 5 for diversity
            max_concurrent = 1 + ((i - 1) % 5)
            worker, _created = Worker.objects.get_or_create(
                name=name,
                defaults={"max_concurrent_tasks": max_concurrent, "is_active": True},
            )
            workers.append(worker)

        # Create tasks
        if tasks_count > 0:
            # Avoid loading all workers if none were requested
            if not workers:
                workers = list(Worker.objects.all())

        for i in range(1, tasks_count + 1):
            priority = random.randint(1, 5)
            description = f"Demo task #{i}"
            Task.objects.create(
                description=description,
                priority=priority,
                status=Task.Status.PENDING,
                assignee=None,
            )

        self.stdout.write(self.style.SUCCESS("Seeding completed."))
        return None
