import Foundation

public struct DiagnosticEngine: Sendable {
    public let faultMode: FaultMode

    public init(faultMode: FaultMode = .none) {
        self.faultMode = faultMode
    }

    public func run(
        _ kind: DiagnosticKind,
        profile: DeviceProfile
    ) async -> DiagnosticResult {
        switch faultMode {
        case .timeout:
            return DiagnosticResult(
                kind: kind,
                status: .failed,
                code: "DIAGNOSTIC_TIMEOUT",
                message: "The \(kind.title.lowercased()) diagnostic exceeded its time budget on \(profile.model)."
            )
        case .sensorUnavailable where kind == .sensor:
            return DiagnosticResult(
                kind: kind,
                status: .failed,
                code: "SENSOR_UNAVAILABLE",
                message: "The requested sensor was unavailable."
            )
        case .corrupted:
            return DiagnosticResult(
                kind: kind,
                status: .failed,
                code: "RESULT_CORRUPTED",
                message: "The diagnostic result failed schema validation."
            )
        case .none, .sensorUnavailable:
            return DiagnosticResult(
                kind: kind,
                status: .passed,
                code: "OK",
                message: "The \(kind.title.lowercased()) diagnostic passed on \(profile.model).",
                measurement: measurement(for: kind)
            )
        }
    }

    private func measurement(for kind: DiagnosticKind) -> Double {
        switch kind {
        case .battery: return 0.93
        case .display: return 1.0
        case .network: return 18.4
        case .sensor: return 0.02
        }
    }
}

