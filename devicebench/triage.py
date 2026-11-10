from __future__ import annotations

import re
from dataclasses import dataclass

from .models import FailureCategory


@dataclass(frozen=True, slots=True)
class TriageDecision:
    category: FailureCategory
    evidence: tuple[str, ...]


_RULES: tuple[tuple[FailureCategory, tuple[re.Pattern[str], ...]], ...] = (
    (
        FailureCategory.INFRASTRUCTURE,
        tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in (
                r"unable to boot (?:the )?simulator",
                r"failed to create simulator",
                r"device is unavailable",
                r"core simulator service.*(?:failed|invalid)",
                r"app installation failed",
                r"unable to install",
                r"info\.plist missing",
                r"xcodebuild: error:",
            )
        ),
    ),
    (
        FailureCategory.APPLICATION_CRASH,
        tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in (
                r"application.*crash",
                r"terminated due to signal",
                r"uncaught exception",
                r"process crashed",
            )
        ),
    ),
    (
        FailureCategory.TIMEOUT,
        tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in (
                r"timed out",
                r"exceeded timeout",
                r"timeout waiting",
                r"exceeded.*time limit",
                r"failed to wait for",
            )
        ),
    ),
    (
        FailureCategory.ASSERTION,
        tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in (
                r"xctassert\w* failed",
                r"test case.*failed",
                r"failed - expected",
                r"assertion failure",
            )
        ),
    ),
)


def classify_failure(log_text: str) -> TriageDecision:
    for category, patterns in _RULES:
        matches: list[str] = []
        for line in log_text.splitlines():
            stripped = line.strip()
            if stripped and any(pattern.search(stripped) for pattern in patterns):
                matches.append(stripped[:240])
            if len(matches) == 3:
                break
        if matches:
            return TriageDecision(category=category, evidence=tuple(matches))
    return TriageDecision(
        category=FailureCategory.UNKNOWN,
        evidence=("No deterministic triage rule matched the test log.",),
    )

