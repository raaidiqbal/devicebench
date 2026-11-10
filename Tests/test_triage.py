import pytest

from devicebench.models import FailureCategory
from devicebench.triage import classify_failure


@pytest.mark.parametrize(
    ("log", "category"),
    [
        ("xcodebuild: error: Unable to boot simulator", FailureCategory.INFRASTRUCTURE),
        (
            "App installation failed: Unable to Install DeviceBench. Info.plist missing",
            FailureCategory.INFRASTRUCTURE,
        ),
        ("The application process crashed after launch", FailureCategory.APPLICATION_CRASH),
        ("Asynchronous wait failed: timed out after 10 seconds", FailureCategory.TIMEOUT),
        ("XCTAssertEqual failed - expected PASS", FailureCategory.ASSERTION),
        ("something novel happened", FailureCategory.UNKNOWN),
    ],
)
def test_failure_classification(log: str, category: FailureCategory) -> None:
    decision = classify_failure(log)

    assert decision.category == category
    assert decision.evidence


def test_infrastructure_wins_over_secondary_assertion() -> None:
    decision = classify_failure(
        "XCTAssertTrue failed\nCore Simulator Service failed while booting the device"
    )

    assert decision.category == FailureCategory.INFRASTRUCTURE

