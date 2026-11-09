from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from typing import Any


class RunStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureCategory(StrEnum):
    ASSERTION = "assertion"
    APPLICATION_CRASH = "application_crash"
    TIMEOUT = "timeout"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


class DeviceHealth(StrEnum):
    AVAILABLE = "available"
    LEASED = "leased"
    QUARANTINED = "quarantined"


@dataclass(frozen=True, slots=True)
class DeviceSpec:
    identifier: str
    name: str
    platform: str
    os_version: str
    model: str
    capabilities: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DeviceSpec":
        required = ("id", "name", "platform", "os", "model")
        missing = [key for key in required if not value.get(key)]
        if missing:
            raise ValueError(f"device is missing required fields: {', '.join(missing)}")
        return cls(
            identifier=str(value["id"]),
            name=str(value["name"]),
            platform=str(value["platform"]),
            os_version=str(value["os"]),
            model=str(value["model"]),
            capabilities=tuple(str(item) for item in value.get("capabilities", ())),
        )

    @property
    def destination(self) -> str:
        return f"platform={self.platform},name={self.model},OS={self.os_version}"


@dataclass(frozen=True, slots=True)
class SuiteSpec:
    name: str
    target: str
    platforms: tuple[str, ...]
    fault_modes: tuple[str, ...] = ("none",)
    retries: int = 0

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SuiteSpec":
        required = ("name", "target", "platforms")
        missing = [key for key in required if not value.get(key)]
        if missing:
            raise ValueError(f"suite is missing required fields: {', '.join(missing)}")
        retries = int(value.get("retries", 0))
        if retries < 0:
            raise ValueError("suite retries cannot be negative")
        modes = tuple(str(item) for item in value.get("fault_modes", ("none",)))
        if not modes:
            raise ValueError("suite must define at least one fault mode")
        return cls(
            name=str(value["name"]),
            target=str(value["target"]),
            platforms=tuple(str(item) for item in value["platforms"]),
            fault_modes=modes,
            retries=retries,
        )


@dataclass(frozen=True, slots=True)
class LabConfig:
    devices: tuple[DeviceSpec, ...]
    suites: tuple[SuiteSpec, ...]


@dataclass(frozen=True, slots=True)
class TestJob:
    job_id: str
    device: DeviceSpec
    suite: SuiteSpec
    fault_mode: str
    attempt: int = 1

    def with_attempt(self, attempt: int) -> "TestJob":
        return replace(self, attempt=attempt)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "attempt": self.attempt,
            "device_id": self.device.identifier,
            "device": self.device.name,
            "destination": self.device.destination,
            "suite": self.suite.name,
            "target": self.suite.target,
            "fault_mode": self.fault_mode,
            "retries": self.suite.retries,
        }


@dataclass(frozen=True, slots=True)
class RunResult:
    job: TestJob
    status: RunStatus
    duration_seconds: float
    category: FailureCategory | None = None
    evidence: tuple[str, ...] = ()
    log_path: Path | None = None
    result_bundle: Path | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == RunStatus.PASSED

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.job.to_dict(),
            "status": self.status.value,
            "duration_seconds": round(self.duration_seconds, 3),
            "category": self.category.value if self.category else None,
            "evidence": list(self.evidence),
            "log_path": str(self.log_path) if self.log_path else None,
            "result_bundle": str(self.result_bundle) if self.result_bundle else None,
            "summary": self.summary,
        }

