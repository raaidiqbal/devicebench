from __future__ import annotations

import json
import re
from pathlib import Path

from .models import DeviceHealth, DeviceSpec, LabConfig, SuiteSpec, TestJob


def load_config(path: Path) -> LabConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("lab config must be a JSON object")
    devices_raw = payload.get("devices")
    suites_raw = payload.get("suites")
    if not isinstance(devices_raw, list) or not devices_raw:
        raise ValueError("lab config must contain at least one device")
    if not isinstance(suites_raw, list) or not suites_raw:
        raise ValueError("lab config must contain at least one suite")

    devices = tuple(DeviceSpec.from_dict(item) for item in devices_raw)
    suites = tuple(SuiteSpec.from_dict(item) for item in suites_raw)
    device_ids = [device.identifier for device in devices]
    if len(device_ids) != len(set(device_ids)):
        raise ValueError("device ids must be unique")
    return LabConfig(devices=devices, suites=suites)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_plan(config: LabConfig) -> tuple[TestJob, ...]:
    jobs: list[TestJob] = []
    for suite in config.suites:
        compatible = [device for device in config.devices if device.platform in suite.platforms]
        if not compatible:
            raise ValueError(f"suite {suite.name!r} has no compatible devices")
        for device in compatible:
            for fault_mode in suite.fault_modes:
                job_id = "-".join((_slug(suite.name), _slug(device.identifier), _slug(fault_mode)))
                jobs.append(
                    TestJob(
                        job_id=job_id,
                        device=device,
                        suite=suite,
                        fault_mode=fault_mode,
                    )
                )
    return tuple(jobs)


class DevicePool:
    """Tracks exclusive simulator leases and quarantine state."""

    def __init__(self, devices: tuple[DeviceSpec, ...]):
        self._health = {device.identifier: DeviceHealth.AVAILABLE for device in devices}

    def acquire(self, device_id: str) -> None:
        state = self._health[device_id]
        if state != DeviceHealth.AVAILABLE:
            raise RuntimeError(f"device {device_id} is {state.value}")
        self._health[device_id] = DeviceHealth.LEASED

    def release(self, device_id: str) -> None:
        if self._health[device_id] != DeviceHealth.LEASED:
            raise RuntimeError(f"device {device_id} does not have an active lease")
        self._health[device_id] = DeviceHealth.AVAILABLE

    def quarantine(self, device_id: str) -> None:
        self._health[device_id] = DeviceHealth.QUARANTINED

    def state(self, device_id: str) -> DeviceHealth:
        return self._health[device_id]

    def snapshot(self) -> dict[str, str]:
        return {device_id: state.value for device_id, state in self._health.items()}

