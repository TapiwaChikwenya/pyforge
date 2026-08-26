import Foundation

enum ServerMode: String, Codable, Sendable {
    case local
    case hosted
}

struct CurriculumResponse: Codable, Sendable {
    var projects: [ProjectSummary]
    var progress: Progress
    let stages: [LearningStage]
    let mode: ServerMode
    let authEnabled: Bool
    let allowAnonymous: Bool
    let firstHour: FirstHour?

    enum CodingKeys: String, CodingKey {
        case projects, progress, stages, mode
        case authEnabled = "auth_enabled"
        case allowAnonymous = "allow_anonymous"
        case firstHour = "first_hour"
    }
}

struct ProjectSummary: Codable, Identifiable, Hashable, Sendable {
    let id: String
    let num: Int
    let title: String
    let tagline: String
    let level: String
    let tech: [String]
    let estimatedHours: Int
    let stackTier: String
    let environmentCommand: String
    var exercisesDone: Int
    let exercisesTotal: Int
    let exerciseIDs: [String]
    var milestonesDone: Int
    let milestonesTotal: Int
    let interviewTotal: Int

    enum CodingKeys: String, CodingKey {
        case id, num, title, tagline, level, tech
        case estimatedHours = "est_hours"
        case stackTier = "stack_tier"
        case environmentCommand = "environment_command"
        case exercisesDone = "exercises_done"
        case exercisesTotal = "exercises_total"
        case exerciseIDs = "exercise_ids"
        case milestonesDone = "milestones_done"
        case milestonesTotal = "milestones_total"
        case interviewTotal = "interview_total"
    }
}

struct Progress: Codable, Sendable {
    var exercises: [String: Bool]
    var milestones: [String: [Int]]
}

struct LearningStage: Codable, Identifiable, Sendable {
    let title: String
    let projectIDs: [String]

    var id: String { title }

    enum CodingKeys: String, CodingKey {
        case title
        case projectIDs = "project_ids"
    }
}

struct FirstHour: Codable, Sendable {
    let projectID: String
    let exerciseID: String
    let title: String
    let blurb: String
    let estimatedMinutes: Int

    enum CodingKeys: String, CodingKey {
        case title, blurb
        case projectID = "project_id"
        case exerciseID = "exercise_id"
        case estimatedMinutes = "est_minutes"
    }
}

struct ProjectResponse: Codable, Sendable {
    let project: Project
    var exercisesPassed: [String: Bool]
    var milestonesDone: [Int]

    enum CodingKeys: String, CodingKey {
        case project
        case exercisesPassed = "exercises_passed"
        case milestonesDone = "milestones_done"
    }
}

struct Project: Codable, Identifiable, Sendable {
    let id: String
    let num: Int
    let title: String
    let tagline: String
    let level: String
    let tech: [String]
    let estimatedHours: Int
    let brief: String
    let milestones: [String]
    let underTheHood: String?
    let environment: ProjectEnvironment
    let exercises: [Exercise]
    let interview: [InterviewQuestion]

    enum CodingKeys: String, CodingKey {
        case id, num, title, tagline, level, tech, brief, milestones, environment, exercises, interview
        case estimatedHours = "est_hours"
        case underTheHood = "under_the_hood"
    }
}

struct ProjectEnvironment: Codable, Sendable {
    let services: [String]
    let command: String
    let note: String
}

struct Exercise: Codable, Identifiable, Sendable {
    let id: String
    let title: String
    let instructions: String
    let starterCode: String
    let refresher: String?
    let objectives: [String]
    let hints: [String]
    let resources: [LearningResource]
    let runtime: String
    let packages: [String]
    let hasCommunitySolutions: Bool

    enum CodingKeys: String, CodingKey {
        case id, title, instructions, refresher, objectives, hints, resources, runtime, packages
        case starterCode = "starter_code"
        case hasCommunitySolutions = "has_community_solutions"
    }
}

struct LearningResource: Codable, Identifiable, Sendable {
    let title: String
    let url: String

    var id: String { url }
}

struct InterviewQuestion: Codable, Identifiable, Sendable {
    let question: String
    let answer: String
    let explanation: String
    let difficulty: String
    let topics: [String]

    var id: String { question }
}

struct HealthResponse: Codable, Sendable {
    let ok: Bool
    let mode: ServerMode
    let projects: Int
}

struct RunResponse: Codable, Sendable {
    let passed: Bool
    let output: String
    let error: String
    let timedOut: Bool

    enum CodingKeys: String, CodingKey {
        case passed, output, error
        case timedOut = "timed_out"
    }
}

struct MilestoneResponse: Codable, Sendable {
    let ok: Bool
    let milestonesDone: [Int]

    enum CodingKeys: String, CodingKey {
        case ok
        case milestonesDone = "milestones_done"
    }
}

struct EmptyResponse: Codable, Sendable {
    let ok: Bool
}
