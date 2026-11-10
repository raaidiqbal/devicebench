import subprocess
from pathlib import Path

import pytest

from devicebench.models import FailureCategory, RunStatus
from devicebench.planner import build_plan, load_config
from devicebench.runner import XcodebuildRunner, build_xcodebuild_command
from devicebench.xcresult import TestSummary as ResultSummary


ROOT = Path(__file__).resolve().parents[1]


def test_xcode_command_is_argument_safe_and_scoped() -> None:
    job = build_plan(load_config(ROOT / "configs" / "lab.ci.json"))[0]
    command = build_xcodebuild_command(
        job,
        project=Path("DeviceBench.xcodeproj"),
        scheme="DeviceBench",
        result_bundle=Path("reports/job.xcresult"),
    )

    assert command[0:2] == ["xcodebuild", "test"]
    assert job.device.destination in command
    assert f"-only-testing:{job.suite.target}" in command
    assert command[-1] == "CODE_SIGNING_ALLOWED=NO"


def test_xcode_command_can_reuse_prebuilt_test_products() -> None:
    job = build_plan(load_config(ROOT / "configs" / "lab.ci.json"))[0]
    command = build_xcodebuild_command(
        job,
        project=Path("DeviceBench.xcodeproj"),
        scheme="DeviceBench",
        result_bundle=Path("reports/job.xcresult"),
        action="test-without-building",
    )

    assert command[0:2] == ["xcodebuild", "test-without-building"]


def test_xcode_runner_converts_process_deadline_to_infrastructure_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    job = build_plan(load_config(ROOT / "configs" / "lab.ci.json"))[1]

    def exceed_deadline(command: list[str], **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=float(kwargs["timeout"]),
            output="partial stdout",
            stderr="simulator stopped responding",
        )

    monkeypatch.setattr(subprocess, "run", exceed_deadline)
    runner = XcodebuildRunner(
        Path("DeviceBench.xcodeproj"),
        "DeviceBench",
        tmp_path,
        timeout_seconds=1,
    )

    result = runner.run(job)

    assert result.status == RunStatus.FAILED
    assert result.category == FailureCategory.INFRASTRUCTURE
    assert result.evidence == ("xcodebuild exceeded the 1-second attempt deadline",)
    assert result.log_path is not None
    assert "partial stdout" in result.log_path.read_text(encoding="utf-8")


def test_xcode_runner_rejects_nonpositive_deadline(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        XcodebuildRunner(Path("project"), "scheme", tmp_path, timeout_seconds=0)


def test_xcode_runner_attaches_normalized_result_bundle_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    job = build_plan(load_config(ROOT / "configs" / "lab.ci.json"))[0]

    def successful_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        bundle = Path(command[command.index("-resultBundlePath") + 1])
        bundle.mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="passed", stderr="")

    monkeypatch.setattr(subprocess, "run", successful_run)
    monkeypatch.setattr(
        "devicebench.runner.read_summary",
        lambda _: ResultSummary(passed=4, failed=0, skipped=1, duration_seconds=1.25),
    )
    runner = XcodebuildRunner(Path("project"), "scheme", tmp_path)

    result = runner.run(job)

    assert result.passed
    assert result.summary == {
        "passed": 4,
        "failed": 0,
        "skipped": 1,
        "total": 5,
        "duration_seconds": 1.25,
    }

