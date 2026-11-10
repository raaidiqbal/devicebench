from collections import deque
from pathlib import Path

from devicebench.models import FailureCategory, RunResult, RunStatus, TestJob as DeviceTestJob
from devicebench.orchestrator import LabCoordinator
from devicebench.planner import DevicePool, build_plan, load_config


ROOT = Path(__file__).resolve().parents[1]


class FakeRunner:
    def __init__(self, outcomes: list[tuple[RunStatus, FailureCategory | None]]):
        self.outcomes = deque(outcomes)

    def run(self, job: DeviceTestJob) -> RunResult:
        status, category = self.outcomes.popleft()
        return RunResult(
            job=job,
            status=status,
            duration_seconds=0.1,
            category=category,
        )


def _retryable_job() -> tuple[object, DeviceTestJob]:
    config = load_config(ROOT / "configs" / "lab.ci.json")
    job = next(job for job in build_plan(config) if job.suite.retries == 1)
    return config, job


def test_infrastructure_failure_retries_then_passes() -> None:
    config, job = _retryable_job()
    runner = FakeRunner(
        [
            (RunStatus.FAILED, FailureCategory.INFRASTRUCTURE),
            (RunStatus.PASSED, None),
        ]
    )
    pool = DevicePool(config.devices)

    results = LabCoordinator(pool, runner).execute((job,))

    assert [result.status for result in results] == [RunStatus.FAILED, RunStatus.PASSED]
    assert results[1].job.attempt == 2
    assert pool.snapshot()[job.device.identifier] == "available"


def test_repeated_infrastructure_failure_quarantines_device() -> None:
    config, job = _retryable_job()
    runner = FakeRunner(
        [
            (RunStatus.FAILED, FailureCategory.INFRASTRUCTURE),
            (RunStatus.FAILED, FailureCategory.INFRASTRUCTURE),
        ]
    )
    pool = DevicePool(config.devices)

    results = LabCoordinator(pool, runner).execute((job,))

    assert len(results) == 2
    assert pool.snapshot()[job.device.identifier] == "quarantined"


def test_assertion_failure_does_not_retry_or_quarantine() -> None:
    config, job = _retryable_job()
    runner = FakeRunner([(RunStatus.FAILED, FailureCategory.ASSERTION)])
    pool = DevicePool(config.devices)

    results = LabCoordinator(pool, runner).execute((job,))

    assert len(results) == 1
    assert pool.snapshot()[job.device.identifier] == "available"


def test_coordinator_emits_every_attempt_to_progress_callback() -> None:
    config, job = _retryable_job()
    runner = FakeRunner(
        [
            (RunStatus.FAILED, FailureCategory.INFRASTRUCTURE),
            (RunStatus.PASSED, None),
        ]
    )
    observed: list[RunResult] = []

    results = LabCoordinator(
        DevicePool(config.devices),
        runner,
        on_result=observed.append,
    ).execute((job,))

    assert observed == list(results)

