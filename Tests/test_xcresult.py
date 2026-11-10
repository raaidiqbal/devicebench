import json
import subprocess
from pathlib import Path

import pytest

from devicebench.xcresult import parse_summary, read_summary


def test_parse_modern_summary_shape() -> None:
    summary = parse_summary(
        {
            "passedTests": 17,
            "failedTests": 2,
            "skippedTests": 1,
            "totalTestDuration": 12.75,
        }
    )

    assert summary.total == 20
    assert summary.failed == 2
    assert summary.duration_seconds == 12.75


def test_parse_nested_legacy_shape() -> None:
    summary = parse_summary(
        {
            "testableSummaries": [
                {
                    "passedTestCount": 4,
                    "failedTestCount": 0,
                    "skippedTestCount": 2,
                    "duration": 3,
                }
            ]
        }
    )

    assert summary.passed == 4
    assert summary.skipped == 2


def test_read_summary_bounds_xcresulttool_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed: dict[str, object] = {}

    def completed(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["timeout"] = kwargs["timeout"]
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"passedTests": 2, "failedTests": 0}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", completed)

    summary = read_summary(tmp_path / "result.xcresult")

    assert summary.passed == 2
    assert observed["timeout"] == 30
    assert observed["command"][0:2] == ["xcrun", "xcresulttool"]

