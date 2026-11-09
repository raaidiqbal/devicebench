import DiagnosticCore
import Foundation

@MainActor
final class DiagnosticViewModel: ObservableObject {
    @Published var selectedKind: DiagnosticKind
    @Published private(set) var result: DiagnosticResult?
    @Published private(set) var repairState: RepairState = .awaitingDiagnosis

    private let engine: DiagnosticEngine
    private let profile: DeviceProfile
    private var workflow = RepairWorkflow()

    init(environment: [String: String] = ProcessInfo.processInfo.environment) {
        let fault = FaultMode(rawValue: environment["DEVICEBENCH_FAULT"] ?? "none") ?? .none
        selectedKind = DiagnosticKind(
            rawValue: environment["DEVICEBENCH_DIAGNOSTIC"] ?? "battery"
        ) ?? .battery
        engine = DiagnosticEngine(faultMode: fault)
        profile = DeviceProfile(
            model: environment["SIMULATOR_MODEL_IDENTIFIER"] ?? "simulated-device",
            osVersion: ProcessInfo.processInfo.operatingSystemVersionString
        )
    }

    var statusText: String {
        result?.status.rawValue.uppercased() ?? "NOT RUN"
    }

    var resultCode: String {
        result?.code ?? "NONE"
    }

    func runDiagnostic() {
        Task {
            result = await engine.run(selectedKind, profile: profile)
            workflow = RepairWorkflow()
            try? workflow.recordDiagnosis()
            repairState = workflow.state
        }
    }

    func authorizeRepair() {
        try? workflow.authorize()
        repairState = workflow.state
    }

    func completeRepair() {
        try? workflow.complete()
        repairState = workflow.state
    }
}

