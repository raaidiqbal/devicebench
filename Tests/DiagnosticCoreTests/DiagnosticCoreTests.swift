import XCTest
@testable import DiagnosticCore

final class DiagnosticCoreTests: XCTestCase {
    private let profile = DeviceProfile(model: "fixture", osVersion: "17.0")

    func testHealthyBatteryDiagnosticPasses() async {
        let result = await DiagnosticEngine().run(.battery, profile: profile)

        XCTAssertEqual(result.status, .passed)
        XCTAssertEqual(result.code, "OK")
        XCTAssertNotNil(result.measurement)
    }

    func testUnavailableSensorIsIsolatedToSensorDiagnostic() async {
        let engine = DiagnosticEngine(faultMode: .sensorUnavailable)

        let sensor = await engine.run(.sensor, profile: profile)
        let battery = await engine.run(.battery, profile: profile)

        XCTAssertEqual(sensor.status, .failed)
        XCTAssertEqual(sensor.code, "SENSOR_UNAVAILABLE")
        XCTAssertEqual(battery.status, .passed)
    }

    func testTimeoutProducesStableFailureCode() async {
        let result = await DiagnosticEngine(faultMode: .timeout).run(.network, profile: profile)

        XCTAssertEqual(result.status, .failed)
        XCTAssertEqual(result.code, "DIAGNOSTIC_TIMEOUT")
    }

    func testRepairWorkflowRequiresOrderedTransitions() throws {
        var workflow = RepairWorkflow()

        XCTAssertThrowsError(try workflow.complete())
        try workflow.recordDiagnosis()
        try workflow.authorize()
        try workflow.complete()

        XCTAssertEqual(workflow.state, .completed)
    }
}

