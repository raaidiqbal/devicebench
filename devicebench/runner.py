from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Protocol

from .models import FailureCategory, RunResult, RunStatus, TestJob
from .triage import classify_failure


class JobRunner(Protocol):
    def run(self, job: TestJob) -> RunResult: ...


def build_xcodebuild_command(
    job: TestJob,
    *,
    project: Path,
    scheme: str,
    result_bundle: Path,
) -> list[str]:
    return [
        "xcodebuild",
        "test",
        "-project",
        str(project),
        "-scheme",
        scheme,
        "-destination",
        job.device.destination,
        "-resultBundlePath",
        str(result_bundle),
        f"-only-testing:{job.suite.target}",
        "CODE_SIGNING_ALLOWED=NO",
    ]


class XcodebuildRunner:
    def __init__(
        self,
        project: Path,
        scheme: str,
        results_dir: Path,
        timeout_seconds: float = 240,
    ):
        self.project = project
        self.scheme = scheme
        self.results_dir = results_dir
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds

    def command_for(self, job: TestJob) -> list[str]:
        bundle = self.results_dir / f"{job.job_id}-attempt-{job.attempt}.xcresult"
        return build_xcodebuild_command(
            job,
            project=self.project,
            scheme=self.scheme,
            result_bundle=bundle,
        )

    def run(self, job: TestJob) -> RunResult:
        self.results_dir.mkdir(parents=True, exist_ok=True)
        bundle = self.results_dir / f"{job.job_id}-attempt-{job.attempt}.xcresult"
        log_path = self.results_dir / f"{job.job_id}-attempt-{job.attempt}.log"
        command = self.command_for(job)
        environment = os.environ.copy()
        environment.update(
            {
                "DEVICEBENCH_FAULT": job.fault_mode,
                "DEVICEBENCH_JOB_ID": job.job_id,
            }
        )

        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            partial_stdout = exc.stdout or ""
            partial_stderr = exc.stderr or ""
            if isinstance(partial_stdout, bytes):
                partial_stdout = partial_stdout.decode("utf-8", errors="replace")
            if isinstance(partial_stderr, bytes):
                partial_stderr = partial_stderr.decode("utf-8", errors="replace")
            message = (
                f"xcodebuild exceeded the {self.timeout_seconds:g}-second attempt deadline"
            )
            combined_log = f"{partial_stdout}\n{partial_stderr}\n{message}".strip()
            log_path.write_text(combined_log, encoding="utf-8")
            return RunResult(
                job=job,
                status=RunStatus.FAILED,
                duration_seconds=duration,
                category=FailureCategory.INFRASTRUCTURE,
                evidence=(message,),
                log_path=log_path,
                result_bundle=bundle if bundle.exists() else None,
            )
        duration = time.monotonic() - started
        combined_log = f"{completed.stdout}\n{completed.stderr}".strip()
        log_path.write_text(combined_log, encoding="utf-8")

        if completed.returncode == 0:
            return RunResult(
                job=job,
                status=RunStatus.PASSED,
                duration_seconds=duration,
                log_path=log_path,
                result_bundle=bundle if bundle.exists() else None,
            )

        decision = classify_failure(combined_log)
        return RunResult(
            job=job,
            status=RunStatus.FAILED,
            duration_seconds=duration,
            category=decision.category,
            evidence=decision.evidence,
            log_path=log_path,
            result_bundle=bundle if bundle.exists() else None,
        )

