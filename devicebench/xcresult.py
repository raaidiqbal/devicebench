from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TestSummary:
    passed: int
    failed: int
    skipped: int
    duration_seconds: float

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped


def _number(payload: dict[str, Any], *keys: str) -> float:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def parse_summary(payload: dict[str, Any]) -> TestSummary:
    metrics = payload.get("testableSummaries", payload)
    if isinstance(metrics, list):
        metrics = metrics[0] if metrics else {}
    if not isinstance(metrics, dict):
        metrics = {}
    return TestSummary(
        passed=int(_number(metrics, "passedTests", "passedTestCount")),
        failed=int(_number(metrics, "failedTests", "failedTestCount")),
        skipped=int(_number(metrics, "skippedTests", "skippedTestCount")),
        duration_seconds=_number(metrics, "totalTestDuration", "duration"),
    )


def read_summary(result_bundle: Path) -> TestSummary:
    completed = subprocess.run(
        [
            "xcrun",
            "xcresulttool",
            "get",
            "test-results",
            "summary",
            "--path",
            str(result_bundle),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ValueError("xcresult summary was not a JSON object")
    return parse_summary(payload)

