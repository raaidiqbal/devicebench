from devicebench.xcresult import parse_summary


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

