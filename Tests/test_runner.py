from pathlib import Path

from devicebench.planner import build_plan, load_config
from devicebench.runner import build_xcodebuild_command


ROOT = Path(__file__).resolve().parents[1]


def test_xcode_command_is_argument_safe_and_scoped() -> None:
    job = build_plan(load_config(ROOT / "configs" / "lab.ci.json"))[0]
    command = build_xcodebuild_command(
        job,
        project=Path("DeviceBench.xcodeproj"),
        scheme="DeviceBench",
        result_bundle=Path("reports/job.xcresult"),
    )

    assert command[0:2] == ["xcodebuild", "test"]
    assert job.device.destination in command
    assert f"-only-testing:{job.suite.target}" in command
    assert command[-1] == "CODE_SIGNING_ALLOWED=NO"

