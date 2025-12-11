import time

from django.core.management.base import BaseCommand

from tasks.services import AssignmentService


class Command(BaseCommand):
    help = "Assign pending tasks to workers and perform autoscaling. Use --loop to run continuously."

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Run continuously in a loop.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=10,
            help="Interval in seconds between iterations when running in --loop mode (default: 10)",
        )

    def handle(self, *args, **options):
        service = AssignmentService()
        loop = options.get("loop", False)
        interval = options.get("interval", 10)

        def run_once():
            added, deactivated = service.autoscale_workers()
            assigned = service.assign_pending_tasks()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Autoscale: +{added}/-{deactivated}; Assigned tasks: {assigned}"
                )
            )

        if not loop:
            run_once()
            return

        self.stdout.write(
            self.style.WARNING(
                f"Running in loop mode (interval={interval}s). Press Ctrl+C to stop."
            )
        )
        try:
            while True:
                run_once()
                time.sleep(max(1, int(interval)))
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("Stopping by user request."))
