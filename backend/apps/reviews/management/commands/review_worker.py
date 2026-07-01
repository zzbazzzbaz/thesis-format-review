from __future__ import annotations

import signal
import time

from django.core.management.base import BaseCommand

from apps.reviews.services.executor import claim_next_pending_task, execute_task


class Command(BaseCommand):
    help = "Run the lightweight SQLite-backed review worker."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=3.0, help="Idle sleep seconds.")
        parser.add_argument("--once", action="store_true", help="Process at most one task.")

    def handle(self, *args, **options):
        interval = options["interval"]
        once = options["once"]
        stopping = False

        def request_stop(signum, frame):
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGINT, request_stop)
        signal.signal(signal.SIGTERM, request_stop)

        self.stdout.write(self.style.SUCCESS("review_worker started"))
        while not stopping:
            task = claim_next_pending_task()
            if task is None:
                if once:
                    break
                time.sleep(interval)
                continue
            self.stdout.write(f"processing task {task.pk}")
            execute_task(task.pk)
            if once:
                break
        self.stdout.write(self.style.SUCCESS("review_worker stopped"))
