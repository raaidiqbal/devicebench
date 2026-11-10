from pathlib import Path

from devicebench.models import FailureCategory, RunResult, RunStatus
from devicebench.planner import build_plan, load_config
from devicebench.report import render_markdown_report, write_markdown_report


ROOT = Path(__file__).resolve().parents[1]


def _jobs():
    return build_plan(load_config(ROOT / "configs" / "lab.ci.json"))


def test_report_reduces_retries_to_final_job_outcomes() -> None:
    job = _jobs()[1]
    results = (
        RunResult(
            job=job.with_attempt(1),
            status=RunStatus.FAILED,
            duration_seconds=3,
            category=FailureCategory.INFRASTRUCTURE,
            evidence=("simulator unavailable",),
        ),
        RunResult(
            job=job.with_attempt(2),
            status=RunStatus.PASSED,
            duration_seconds=2,
            summary={"passed": 1, "failed": 0, "skipped": 0},
        ),
    )

    report = render_markdown_report(results)

    assert "**Overall: PASS**" in report
    assert "Final jobs passed: **1/1**" in report
    assert "Execution attempts: **2**" in report
    assert "1 passed / 0 failed / 0 skipped" in report
    assert "Failure evidence" not in report


def test_report_includes_failure_evidence_and_escapes_table_cells() -> None:
    job = _jobs()[2]
    result = RunResult(
        job=job,
        status=RunStatus.FAILED,
        duration_seconds=4.25,
        category=FailureCategory.ASSERTION,
        evidence=("expected PASS | observed FAIL\nsecond line",),
    )

    report = render_markdown_report((result,))

    assert "**Overall: FAIL**" in report
    assert "FAILED (assertion)" in report
    assert r"expected PASS \| observed FAIL second line" in report


def test_empty_report_is_explicit() -> None:
    assert "**Overall: NO RESULTS**" in render_markdown_report(())


def test_write_report_creates_parent_directory(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "report.md"

    write_markdown_report((), output)

    assert output.read_text(encoding="utf-8").startswith("# DeviceBench")
