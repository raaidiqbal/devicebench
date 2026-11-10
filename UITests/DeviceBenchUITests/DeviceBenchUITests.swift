import XCTest

final class DeviceBenchUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
    }

    private func launch(fault: String, diagnostic: String) {
        app.launchEnvironment["DEVICEBENCH_FAULT"] = fault
        app.launchEnvironment["DEVICEBENCH_DIAGNOSTIC"] = diagnostic
        app.launch()
    }

    private func waitForLabel(_ identifier: String, toEqual value: String) {
        let element = app.descendants(matching: .any)[identifier]
        let predicate = NSPredicate(
            format: "exists == true AND (label == %@ OR value == %@)",
            value,
            value
        )
        expectation(for: predicate, evaluatedWith: element)
        waitForExpectations(timeout: 10)
    }

    func testHealthyDiagnosticAndRepairWorkflow() {
        launch(fault: "none", diagnostic: "battery")

        app.buttons["runDiagnosticButton"].tap()
        waitForLabel("statusLabel", toEqual: "PASSED")
        app.buttons["authorizeRepairButton"].tap()
        app.buttons["completeRepairButton"].tap()
        waitForLabel("repairStateLabel", toEqual: "COMPLETED")
    }

    func testSensorFaultReportsStableCode() {
        launch(fault: "sensor_unavailable", diagnostic: "sensor")

        app.buttons["runDiagnosticButton"].tap()
        waitForLabel("statusLabel", toEqual: "FAILED")
        waitForLabel("resultCodeLabel", toEqual: "SENSOR_UNAVAILABLE")
    }

    func testTimeoutReportsStableCode() {
        launch(fault: "timeout", diagnostic: "network")

        app.buttons["runDiagnosticButton"].tap()
        waitForLabel("statusLabel", toEqual: "FAILED")
        waitForLabel("resultCodeLabel", toEqual: "DIAGNOSTIC_TIMEOUT")
    }
}

