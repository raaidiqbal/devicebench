import json
from pathlib import Path

import pytest

from devicebench.models import DeviceHealth
from devicebench.planner import DevicePool, build_plan, load_config


ROOT = Path(__file__).resolve().parents[1]


def test_full_config_expands_to_eight_jobs() -> None:
    config = load_config(ROOT / "configs" / "lab.json")
    jobs = build_plan(config)

    assert len(jobs) == 8
    assert len({job.job_id for job in jobs}) == 8
    assert {job.fault_mode for job in jobs} == {"none", "sensor_unavailable", "timeout"}


def test_duplicate_device_ids_are_rejected(tmp_path: Path) -> None:
    payload = {
        "devices": [
            {"id": "same", "name": "a", "platform": "iOS Simulator", "os": "latest", "model": "A"},
            {"id": "same", "name": "b", "platform": "iOS Simulator", "os": "latest", "model": "B"},
        ],
        "suites": [{"name": "suite", "target": "Tests", "platforms": ["iOS Simulator"]}],
    }
    path = tmp_path / "lab.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unique"):
        load_config(path)


def test_pool_enforces_exclusive_lease_and_quarantine() -> None:
    config = load_config(ROOT / "configs" / "lab.ci.json")
    device_id = config.devices[0].identifier
    pool = DevicePool(config.devices)

    pool.acquire(device_id)
    assert pool.state(device_id) == DeviceHealth.LEASED
    with pytest.raises(RuntimeError, match="leased"):
        pool.acquire(device_id)
    pool.quarantine(device_id)
    assert pool.state(device_id) == DeviceHealth.QUARANTINED

