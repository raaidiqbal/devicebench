# DeviceBench

[![CI](https://github.com/raaidiqbal/devicebench/actions/workflows/ci.yml/badge.svg)](https://github.com/raaidiqbal/devicebench/actions/workflows/ci.yml)

DeviceBench is a simulator-first diagnostic automation lab for testing device health and repair workflows. A Swift fixture app exposes deterministic diagnostic behavior; XCTest and XCUITest validate it; and a Python controller plans simulator matrices, leases devices, retries infrastructure failures, quarantines unhealthy workers, and preserves test evidence.

The project is deliberately built as an automation system rather than a collection of UI tests. It models the operational problems behind a shared device lab: exclusive access, repeatable fault injection, failure classification, test artifacts, and CI-friendly execution.

## What it demonstrates

- Swift diagnostic and repair-domain modeling
- XCTest unit tests and XCUITest end-to-end workflows
- Python test orchestration and helper tooling
- `xcodebuild`, `xcrun`, XcodeGen, and `.xcresult` handling
- Simulator leasing, retry policy, and quarantine state
- Hard per-attempt deadlines so wedged simulator processes cannot stall the lab
- Normalized XCTest counts and a Markdown diagnostic report in every CI summary
- Deterministic triage of assertion, crash, timeout, and infrastructure failures
- GitHub Actions on a macOS runner with retained logs and result bundles
- Stable accessibility identifiers and fault-injected test design

## Architecture

```text
configs/lab*.json
        |
        v
Python matrix planner -> device lease -> xcodebuild -> .xcresult + log
        |                                      |
        |                                      v
        +---------------------------- deterministic triage
                                               |
                                               v
                                  summary.json + CI artifacts

SwiftUI fixture app <- XCUITest <- injected diagnostic/repair scenarios
        |
        v
DiagnosticCore <- XCTest <- state transitions and failure contracts
```

See [docs/architecture.md](docs/architecture.md) for the component boundaries and failure policy.

## Quick start

The Python controller and its tests run on Windows, Linux, or macOS:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m devicebench plan --config configs/lab.json
python -m devicebench run --config configs/lab.ci.json --dry-run
```

Running the Swift and UI tests requires macOS with Xcode and XcodeGen:

```bash
brew install xcodegen
xcodegen generate --spec spec.yml
python -m devicebench run --config configs/lab.ci.json --results reports --attempt-timeout 600
```

The same flow runs automatically on GitHub's `macos-15` hosted runner. CI builds the test products once and runs each isolated lab job with `test-without-building`; simulator tests do not require code signing.

## Diagnostic contracts

The fixture currently models four diagnostics: battery, display, network, and sensor. Fault injection is deterministic:

- `none` returns a passing result with a measurement.
- `sensor_unavailable` fails only the sensor diagnostic.
- `timeout` returns a stable `DIAGNOSTIC_TIMEOUT` code.
- `corrupted` returns a stable schema-validation failure.

The repair workflow permits only `awaiting_diagnosis -> diagnosed -> authorized -> completed`. Invalid transitions fail instead of silently advancing state.

## Lab behavior

Every test job is bound to one simulator record and one exact XCTest identifier. The controller:

1. Acquires an exclusive lease.
2. Runs a scoped `xcodebuild test` command.
3. Preserves the log and result bundle.
4. Retries infrastructure failures only.
5. Quarantines a simulator after its retry budget is exhausted.
6. Terminates an attempt that exceeds its configured execution deadline.
7. Does not retry product assertions, because repeating a deterministic failure would hide the defect.

Every completed attempt prints a concise progress line. At the end of a run,
`reports/summary.json` remains the machine-readable source of truth and
`reports/report.md` provides a human-readable view that GitHub Actions publishes
in the job summary.

## Current boundary

Version 0.1 is simulator-first. It does not claim to manage a physical Apple device fleet, USB relays, or hardware recovery. The controller is intentionally structured so a physical-device backend can be added without changing test planning or triage policy.

## Repository map

```text
Sources/                 Swift core and fixture app
Tests/                   XCTest unit tests
UITests/                 XCUITest workflows
devicebench/             Python planner, runner, coordinator, and triage
configs/                 Full and CI lab matrices
docs/                    Human-facing architecture notes
.github/workflows/       Python and macOS simulator CI
```

## License

MIT

