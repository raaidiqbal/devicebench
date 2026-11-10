# Architecture

## Design goals

DeviceBench separates test intent from execution infrastructure. Test scenarios are declared in JSON, expanded into immutable jobs, and executed through a runner interface. The same plan can target a local simulator, a hosted macOS worker, or a future physical-device backend.

## Python control plane

`planner.py` validates configuration and expands every compatible device, suite, and fault mode into a stable job identifier. `DevicePool` owns the state machine for exclusive leases and quarantine.

`orchestrator.py` applies the retry policy. Only infrastructure failures are retried. Assertion, timeout, and application failures are treated as product or test defects and immediately returned. Repeated infrastructure failure consumes the retry budget and quarantines the device record.

`runner.py` constructs `xcodebuild` arguments as a list rather than a shell string, which avoids quoting and command-injection problems. Each attempt receives a unique log and `.xcresult` path.
It also enforces a per-attempt process deadline. A wedged `xcodebuild` invocation is recorded as an infrastructure failure so the coordinator can retry it and quarantine the simulator if recovery fails.

`triage.py` classifies failures using ordered, deterministic rules and returns the exact matching log lines as evidence. The classifier does not decide whether a test passed; the `xcodebuild` exit status remains authoritative.

`xcresult.py` normalizes modern and legacy summary field names. This keeps reporting logic separate from the execution path and makes captured result payloads independently testable.
Result extraction has its own short deadline; a slow or malformed result bundle cannot block the lab, and the raw bundle remains available for later inspection.

`report.py` reduces attempt-level results to final job outcomes and renders a deterministic Markdown report. The report is a presentation layer only; `summary.json`, `xcodebuild` exit status, and the retained result bundles remain authoritative.

## Swift test fixture

`DiagnosticCore` defines diagnostic kinds, stable result codes, deterministic fault modes, and the repair workflow state machine. It contains no UI dependency and is covered by XCTest.

`DiagnosticFixtureApp` is a small SwiftUI client. It reads launch-time fault configuration and exposes stable accessibility identifiers for all test-critical controls and results.

`DeviceBenchUITests` drives complete diagnostic and repair workflows. Fault cases are separate test methods, allowing the Python controller to select an exact test through Xcode's `-only-testing` interface.

## CI evidence

The Linux job validates the controller independently. The macOS job generates the Xcode project from `spec.yml`, records the selected Xcode and simulator inventory, builds test products once, executes each CI matrix entry with `test-without-building`, and uploads logs plus `.xcresult` bundles even when a test fails.

## Failure taxonomy

- `assertion`: the observed application behavior violated a test contract.
- `application_crash`: the fixture process terminated unexpectedly.
- `timeout`: an expected state did not arrive before the deadline.
- `infrastructure`: simulator or Xcode infrastructure could not execute the test.
- `unknown`: evidence exists but no deterministic rule matched it.

The taxonomy is intentionally small. New categories should be added only when they change retry, quarantine, or ownership behavior.

