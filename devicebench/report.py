from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .models import RunResult


def _escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _final_results(results: Sequence[RunResult]) -> list[RunResult]:
    final_by_job: dict[str, RunResult] = {}
    for result in results:
        final_by_job[result.job.job_id] = result
    return list(final_by_job.values())


def _attempts_by_job(results: Sequence[RunResult]) -> dict[str, int]:
    attempts: dict[str, int] = {}
    for result in results:
        job_id = result.job.job_id
        attempts[job_id] = max(attempts.get(job_id, 0), result.job.attempt)
    return attempts


def _xctest_counts(summary: dict[str, object]) -> str:
    keys = ("passed", "failed", "skipped")
    if not any(key in summary for key in keys):
        return "—"
    return " / ".join(f"{int(summary.get(key, 0))} {key}" for key in keys)


def render_markdown_report(results: Sequence[RunResult]) -> str:
    final = _final_results(results)
    attempts = _attempts_by_job(results)
    passed = sum(result.passed for result in final)
    if not final:
        overall = "NO RESULTS"
    else:
        overall = "PASS" if passed == len(final) else "FAIL"
    total_duration = sum(result.duration_seconds for result in results)

    lines = [
        "# DeviceBench diagnostic lab report",
        "",
        f"**Overall: {overall}**",
        "",
        f"- Final jobs passed: **{passed}/{len(final)}**",
        f"- Execution attempts: **{len(results)}**",
        f"- Controller-observed duration: **{total_duration:.1f}s**",
        "",
        "| Suite | Device | Fault mode | Attempts | Status | XCTest results | Duration |",
        "|---|---|---|---:|---|---|---:|",
    ]

    for result in final:
        status = result.status.value.upper()
        if result.category:
            status = f"{status} ({result.category.value})"
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape(result.job.suite.name),
                    _escape(result.job.device.name),
                    _escape(result.job.fault_mode),
                    str(attempts[result.job.job_id]),
                    _escape(status),
                    _escape(_xctest_counts(result.summary)),
                    f"{result.duration_seconds:.1f}s",
                )
            )
            + " |"
        )

    failures = [result for result in final if not result.passed]
    if failures:
        lines.extend(("", "## Failure evidence", ""))
        for result in failures:
            lines.append(f"### `{_escape(result.job.job_id)}`")
            lines.append("")
            for evidence in result.evidence or ("No deterministic evidence was captured.",):
                lines.append(f"- {_escape(evidence)}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(results: Sequence[RunResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(results), encoding="utf-8")
