import Foundation

struct PyForgeAPI: Sendable {
    let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        decoder = JSONDecoder()
        encoder = JSONEncoder()
    }

    static func normalizedURL(from input: String) -> URL? {
        let trimmed = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        let candidate = trimmed.contains("://") ? trimmed : "http://\(trimmed)"
        guard var components = URLComponents(string: candidate),
              let scheme = components.scheme?.lowercased(),
              scheme == "http" || scheme == "https",
              components.host != nil else { return nil }
        components.path = components.path.replacingOccurrences(of: "/+$", with: "", options: .regularExpression)
        components.query = nil
        components.fragment = nil
        return components.url
    }

    func health() async throws -> HealthResponse {
        try await request(path: "healthz")
    }

    func curriculum() async throws -> CurriculumResponse {
        try await request(path: "api/curriculum")
    }

    func project(id: String) async throws -> ProjectResponse {
        try await request(path: "api/project/\(id)")
    }

    func run(projectID: String, exerciseID: String, code: String) async throws -> RunResponse {
        try await request(
            path: "api/run",
            method: "POST",
            body: RunRequest(projectID: projectID, exerciseID: exerciseID, code: code)
        )
    }

    func setMilestone(projectID: String, index: Int, done: Bool) async throws -> MilestoneResponse {
        try await request(
            path: "api/milestone",
            method: "POST",
            body: MilestoneRequest(projectID: projectID, index: index, done: done)
        )
    }

    private func request<Response: Decodable>(path: String) async throws -> Response {
        var request = URLRequest(url: endpoint(path))
        request.timeoutInterval = 20
        return try await perform(request)
    }

    private func request<Body: Encodable, Response: Decodable>(
        path: String,
        method: String,
        body: Body
    ) async throws -> Response {
        var request = URLRequest(url: endpoint(path))
        request.httpMethod = method
        request.timeoutInterval = 190
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = try encoder.encode(body)
        return try await perform(request)
    }

    private func perform<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            guard (200..<300).contains(http.statusCode) else {
                let detail = (try? decoder.decode(ErrorEnvelope.self, from: data).detail)
                throw APIError.http(status: http.statusCode, detail: detail)
            }
            do {
                return try decoder.decode(Response.self, from: data)
            } catch {
                throw APIError.decoding(error.localizedDescription)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.transport(error.localizedDescription)
        }
    }

    private func endpoint(_ path: String) -> URL {
        baseURL.appending(path: path.trimmingCharacters(in: CharacterSet(charactersIn: "/")))
    }
}
private struct RunRequest: Encodable {
    let projectID: String
    let exerciseID: String
    let code: String

    enum CodingKeys: String, CodingKey {
        case projectID = "project_id"
        case exerciseID = "exercise_id"
        case code
    }
}

private struct MilestoneRequest: Encodable {
    let projectID: String
    let index: Int
    let done: Bool

    enum CodingKeys: String, CodingKey {
        case projectID = "project_id"
        case index, done
    }
}

private struct ErrorEnvelope: Decodable {
    let detail: String?
}

enum APIError: LocalizedError, Equatable {
    case invalidURL
    case invalidResponse
    case transport(String)
    case http(status: Int, detail: String?)
    case decoding(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            "Enter a valid HTTP or HTTPS server address."
        case .invalidResponse:
            "The server returned an invalid response."
        case .transport(let message):
            "Could not reach PyForge. \(message)"
        case .http(let status, let detail):
            detail.map { "Server error \(status): \($0)" } ?? "Server error \(status)."
        case .decoding(let message):
            "The server response is not compatible with this app. \(message)"
        }
    }
}
