import DiagnosticCore
import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = DiagnosticViewModel()

    var body: some View {
        NavigationStack {
            Form {
                Section("Diagnostic") {
                    Picker("Diagnostic type", selection: $viewModel.selectedKind) {
                        ForEach(DiagnosticKind.allCases, id: \.self) { kind in
                            Text(kind.title).tag(kind)
                        }
                    }
                    .accessibilityIdentifier("diagnosticPicker")

                    Button("Run diagnostic") {
                        viewModel.runDiagnostic()
                    }
                    .accessibilityIdentifier("runDiagnosticButton")
                }

                Section("Result") {
                    LabeledContent("Status") {
                        Text(viewModel.statusText)
                            .accessibilityIdentifier("statusLabel")
                            .accessibilityLabel(viewModel.statusText)
                            .accessibilityValue(viewModel.statusText)
                    }
                    LabeledContent("Code") {
                        Text(viewModel.resultCode)
                            .accessibilityIdentifier("resultCodeLabel")
                            .accessibilityLabel(viewModel.resultCode)
                            .accessibilityValue(viewModel.resultCode)
                    }
                    if let message = viewModel.result?.message {
                        Text(message)
                            .accessibilityIdentifier("resultMessageLabel")
                    }
                }

                Section("Repair workflow") {
                    Text(viewModel.repairState.rawValue.uppercased())
                        .accessibilityIdentifier("repairStateLabel")
                        .accessibilityLabel(viewModel.repairState.rawValue.uppercased())
                        .accessibilityValue(viewModel.repairState.rawValue.uppercased())
                    Button("Authorize repair") {
                        viewModel.authorizeRepair()
                    }
                    .disabled(viewModel.repairState != .diagnosed)
                    .accessibilityIdentifier("authorizeRepairButton")
                    Button("Complete repair") {
                        viewModel.completeRepair()
                    }
                    .disabled(viewModel.repairState != .authorized)
                    .accessibilityIdentifier("completeRepairButton")
                }
            }
            .navigationTitle("DeviceBench")
        }
    }
}

#Preview {
    ContentView()
}

