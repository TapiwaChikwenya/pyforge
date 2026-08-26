import XCTest
@testable import PyForge

final class APIModelsTests: XCTestCase {
    func testNormalizesServerAddress() {
        XCTAssertEqual(
            PyForgeAPI.normalizedURL(from: "my-mac.local:8000/")?.absoluteString,
            "http://my-mac.local:8000"
        )
        XCTAssertEqual(
            PyForgeAPI.normalizedURL(from: "https://learn.example.com/path?ignored=1")?.absoluteString,
            "https://learn.example.com/path"
        )
        XCTAssertNil(PyForgeAPI.normalizedURL(from: "ftp://example.com"))
        XCTAssertNil(PyForgeAPI.normalizedURL(from: ""))
    }

    func testDecodesCurriculumContract() throws {
        let json = #"""
        {
          "projects": [{
            "id":"task-forge", "num":1, "title":"Task Forge", "tagline":"Build it",
            "level":"Intermediate", "tech":["Python"], "est_hours":4,
            "stack_tier":"light", "environment_command":"docker compose up",
            "exercises_done":1, "exercises_total":3, "exercise_ids":["tf-1","tf-2","tf-3"],
            "milestones_done":0, "milestones_total":5, "interview_total":3
          }],
          "progress":{"exercises":{"tf-1":true},"milestones":{}},
          "stages":[{"title":"Stage 1", "project_ids":["task-forge"]}],
          "mode":"local", "auth_enabled":false, "allow_anonymous":true,
          "first_hour":{"project_id":"task-forge","exercise_id":"tf-1","title":"Your first hour","blurb":"Start","est_minutes":10}
        }
        """#.data(using: .utf8)!

        let response = try JSONDecoder().decode(CurriculumResponse.self, from: json)

        XCTAssertEqual(response.mode, .local)
        XCTAssertEqual(response.projects.first?.exercisesDone, 1)
        XCTAssertEqual(response.stages.first?.projectIDs, ["task-forge"])
        XCTAssertEqual(response.firstHour?.exerciseID, "tf-1")
    }

    func testDecodesExerciseRunResult() throws {
        let data = #"{"passed":false,"output":"hello","error":"AssertionError","timed_out":false}"#.data(using: .utf8)!
        let result = try JSONDecoder().decode(RunResponse.self, from: data)
        XCTAssertFalse(result.passed)
        XCTAssertEqual(result.output, "hello")
        XCTAssertEqual(result.error, "AssertionError")
        XCTAssertFalse(result.timedOut)
    }
}
