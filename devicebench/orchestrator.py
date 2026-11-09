from __future__ import annotations

from .models import FailureCategory, RunResult, RunStatus, TestJob
from .planner import DevicePool
from .runner import JobRunner


class LabCoordinator:
    def __init__(self, pool: DevicePool, runner: JobRunner):
        self.pool = pool
        self.runner = runner

    def execute(self, jobs: tuple[TestJob, ...]) -> tuple[RunResult, ...]:
        results: list[RunResult] = []
        for base_job in jobs:
            device_id = base_job.device.identifier
            max_attempts = base_job.suite.retries + 1
            for attempt in range(1, max_attempts + 1):
                job = base_job.with_attempt(attempt)
                try:
                    self.pool.acquire(device_id)
                except RuntimeError as exc:
                    results.append(
                        RunResult(
                            job=job,
                            status=RunStatus.SKIPPED,
                            duration_seconds=0,
                            category=FailureCategory.INFRASTRUCTURE,
                            evidence=(str(exc),),
                        )
                    )
                    break

                try:
                    result = self.runner.run(job)
                except Exception as exc:
                    result = RunResult(
                        job=job,
                        status=RunStatus.FAILED,
                        duration_seconds=0,
                        category=FailureCategory.INFRASTRUCTURE,
                        evidence=(f"runner raised {type(exc).__name__}: {exc}",),
                    )
                results.append(result)

                if result.passed:
                    self.pool.release(device_id)
                    break
                if result.category != FailureCategory.INFRASTRUCTURE:
                    self.pool.release(device_id)
                    break
                if attempt < max_attempts:
                    self.pool.release(device_id)
                    continue
                self.pool.quarantine(device_id)
        return tuple(results)

