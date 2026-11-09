import Foundation

public enum DiagnosticKind: String, CaseIterable, Codable, Sendable {
    case battery
    case display
    case network
    case sensor

    public var title: String {
        rawValue.capitalized
    }
}

public enum FaultMode: String, CaseIterable, Codable, Sendable {
    case none
    case sensorUnavailable = "sensor_unavailable"
    case timeout
    case corrupted
}

public enum DiagnosticStatus: String, Codable, Sendable {
    case passed
    case failed
}

public struct DeviceProfile: Equatable, Codable, Sendable {
    public let model: String
    public let osVersion: String

    public init(model: String, osVersion: String) {
        self.model = model
        self.osVersion = osVersion
    }
}

public struct DiagnosticResult: Equatable, Codable, Sendable {
    public let kind: DiagnosticKind
    public let status: DiagnosticStatus
    public let code: String
    public let message: String
    public let measurement: Double?

    public init(
        kind: DiagnosticKind,
        status: DiagnosticStatus,
        code: String,
        message: String,
        measurement: Double? = nil
    ) {
        self.kind = kind
        self.status = status
        self.code = code
        self.message = message
        self.measurement = measurement
    }
}

public enum RepairState: String, Codable, Sendable {
    case awaitingDiagnosis = "awaiting_diagnosis"
    case diagnosed
    case authorized
    case completed
}

public enum RepairWorkflowError: Error, Equatable {
    case invalidTransition(from: RepairState, to: RepairState)
}

public struct RepairWorkflow: Equatable, Sendable {
    public private(set) var state: RepairState = .awaitingDiagnosis

    public init() {}

    public mutating func recordDiagnosis() throws {
        try transition(from: .awaitingDiagnosis, to: .diagnosed)
    }

    public mutating func authorize() throws {
        try transition(from: .diagnosed, to: .authorized)
    }

    public mutating func complete() throws {
        try transition(from: .authorized, to: .completed)
    }

    private mutating func transition(from expected: RepairState, to next: RepairState) throws {
        guard state == expected else {
            throw RepairWorkflowError.invalidTransition(from: state, to: next)
        }
        state = next
    }
}

