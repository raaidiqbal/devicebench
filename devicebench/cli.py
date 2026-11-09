from __future__ import annotations

import argparse
import json
from pathlib import Path

from .orchestrator import LabCoordinator
from .planner import DevicePool, build_plan, load_config
from .runner import XcodebuildRunner
from .triage import classify_failure


def _write_json(payload: object, path: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if path is None:
        print(rendered)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{rendered}\n", encoding="utf-8")
    print(f"wrote {path}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devicebench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="expand a lab config into deterministic jobs")
    plan.add_argument("--config", type=Path, default=Path("configs/lab.json"))
    plan.add_argument("--output", type=Path)

    run = subparsers.add_parser("run", help="run an Xcode test matrix")
    run.add_argument("--config", type=Path, default=Path("configs/lab.ci.json"))
    run.add_argument("--project", type=Path, default=Path("DeviceBench.xcodeproj"))
    run.add_argument("--scheme", default="DeviceBench")
    run.add_argument("--results", type=Path, default=Path("reports"))
    run.add_argument("--dry-run", action="store_true")

    triage = subparsers.add_parser("triage", help="classify an xcodebuild test log")
    triage.add_argument("--log", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "plan":
        config = load_config(args.config)
        jobs = build_plan(config)
        _write_json([job.to_dict() for job in jobs], args.output)
        return 0

    if args.command == "triage":
        decision = classify_failure(args.log.read_text(encoding="utf-8", errors="replace"))
        _write_json(
            {"category": decision.category.value, "evidence": list(decision.evidence)},
            None,
        )
        return 0

    config = load_config(args.config)
    jobs = build_plan(config)
    runner = XcodebuildRunner(args.project, args.scheme, args.results)
    if args.dry_run:
        _write_json(
            [
                {**job.to_dict(), "command": runner.command_for(job)}
                for job in jobs
            ],
            None,
        )
        return 0

    coordinator = LabCoordinator(DevicePool(config.devices), runner)
    results = coordinator.execute(jobs)
    summary_path = args.results / "summary.json"
    _write_json([result.to_dict() for result in results], summary_path)
    return 0 if all(result.passed for result in results) else 1

