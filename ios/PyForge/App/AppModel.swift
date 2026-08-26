import Foundation
import SwiftUI

@MainActor
final class AppModel: ObservableObject {
    static let serverURLKey = "pyforge.serverURL"
    static let defaultServerURL = "http://127.0.0.1:8000"

    @Published private(set) var curriculum: CurriculumResponse?
    @Published private(set) var connectionState: ConnectionState = .idle
    @Published var presentedError: AppError?

    @AppStorage("pyforge.serverURL") var serverURLString = "http://127.0.0.1:8000"

    var api: PyForgeAPI? {
        guard let url = PyForgeAPI.normalizedURL(from: serverURLString) else { return nil }
        return PyForgeAPI(baseURL: url)
    }

    var completedExercises: Int {
        curriculum?.progress.exercises.values.filter { $0 }.count ?? 0
    }

    var totalExercises: Int {
        curriculum?.projects.reduce(0) { $0 + $1.exercisesTotal } ?? 0
    }

    var overallProgress: Double {
        guard totalExercises > 0 else { return 0 }
        return Double(completedExercises) / Double(totalExercises)
    }

    func start() async {
        guard curriculum == nil else { return }
        await refresh()
    }

    func refresh() async {
        guard let api else {
            connectionState = .failed("Invalid server address")
            return
        }
        connectionState = .loading
        do {
            let payload = try await api.curriculum()
            curriculum = payload
            connectionState = .connected(mode: payload.mode)
        } catch {
            connectionState = .failed(error.localizedDescription)
        }
    }

    func testAndSaveServer(_ input: String) async throws -> HealthResponse {
        guard let url = PyForgeAPI.normalizedURL(from: input) else { throw APIError.invalidURL }
        let api = PyForgeAPI(baseURL: url)
        let health = try await api.health()
        serverURLString = url.absoluteString
        curriculum = nil
        await refresh()
        return health
    }

    func loadProject(id: String) async throws -> ProjectResponse {
        guard let api else { throw APIError.invalidURL }
        return try await api.project(id: id)
    }

    func run(projectID: String, exercise: Exercise, code: String) async throws -> RunResponse {
        guard curriculum?.mode == .local else {
            throw APIError.http(status: 404, detail: "Exercise execution requires a local-mode PyForge server.")
        }
        guard let api else { throw APIError.invalidURL }
        let result = try await api.run(projectID: projectID, exerciseID: exercise.id, code: code)
        if result.passed {
            markExercisePassed(exercise.id)
            await refresh()
        }
        return result
    }

    func setMilestone(projectID: String, index: Int, done: Bool) async throws -> [Int] {
        guard let api else { throw APIError.invalidURL }
        let response = try await api.setMilestone(projectID: projectID, index: index, done: done)
        if var payload = curriculum {
            payload.progress.milestones[projectID] = response.milestonesDone
            if let position = payload.projects.firstIndex(where: { $0.id == projectID }) {
                payload.projects[position].milestonesDone = response.milestonesDone.count
            }
            curriculum = payload
        }
        return response.milestonesDone
    }

    func show(_ error: Error) {
        presentedError = AppError(message: error.localizedDescription)
    }

    private func markExercisePassed(_ id: String) {
        guard var payload = curriculum else { return }
        payload.progress.exercises[id] = true
        if let position = payload.projects.firstIndex(where: { $0.exerciseIDs.contains(id) }) {
            payload.projects[position].exercisesDone = payload.projects[position].exerciseIDs
                .filter { payload.progress.exercises[$0] == true }.count
        }
        curriculum = payload
    }
}

enum ConnectionState: Equatable {
    case idle
    case loading
    case connected(mode: ServerMode)
    case failed(String)
}

struct AppError: Identifiable {
    let id = UUID()
    let message: String
}
