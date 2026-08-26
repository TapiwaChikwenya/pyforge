import SwiftUI

struct ProjectDetailView: View {
    let summary: ProjectSummary
    var initialExerciseID: String? = nil

    @EnvironmentObject private var model: AppModel
    @State private var response: ProjectResponse?
    @State private var isLoading = true
    @State private var loadError: String?
    @State private var selectedSection: ProjectSection = .overview

    var body: some View {
        ZStack {
            ForgeBackground()
            Group {
                if isLoading {
                    ProgressView("Loading project…")
                        .tint(ForgeTheme.ember)
                } else if let loadError {
                    ContentUnavailableView("Could not load project", systemImage: "exclamationmark.triangle", description: Text(loadError))
                } else if let response {
                    projectContent(response)
                }
            }
        }
        .navigationTitle(summary.title)
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
    }

    @ViewBuilder
    private func projectContent(_ response: ProjectResponse) -> some View {
        VStack(spacing: 0) {
            ProjectIdentityBar(project: response.project, passed: response.exercisesPassed)
            ProjectSectionPicker(selection: $selectedSection)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

            switch selectedSection {
            case .overview:
                ProjectOverviewView(project: response.project)
            case .exercises:
                ExerciseListView(project: response.project, passed: response.exercisesPassed)
            case .milestones:
                MilestonesView(project: response.project, completed: response.milestonesDone) { completed in
                    self.response?.milestonesDone = completed
                }
            case .interview:
                InterviewView(questions: response.project.interview)
            }
        }
        .onAppear {
            if initialExerciseID != nil { selectedSection = .exercises }
        }
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            response = try await model.loadProject(id: summary.id)
            loadError = nil
        } catch {
            loadError = error.localizedDescription
        }
    }
}

private enum ProjectSection: String, CaseIterable, Identifiable {
    case overview, exercises, milestones, interview
    var id: Self { self }
    var title: String {
        switch self {
        case .overview: "Brief"
        case .exercises: "Code"
        case .milestones: "Build"
        case .interview: "Review"
        }
    }
    var icon: String {
        switch self {
        case .overview: "doc.text"
        case .exercises: "chevron.left.forwardslash.chevron.right"
        case .milestones: "hammer"
        case .interview: "bubble.left.and.bubble.right"
        }
    }
}

private struct ProjectIdentityBar: View {
    let project: Project
    let passed: [String: Bool]

    private var completed: Int { passed.values.filter { $0 }.count }

    var body: some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .fill(ForgeTheme.midnightGradient)
                Text(String(format: "%02d", project.num))
                    .font(.subheadline.bold().monospacedDigit())
                    .foregroundStyle(ForgeTheme.emberLight)
            }
            .frame(width: 48, height: 48)

            VStack(alignment: .leading, spacing: 3) {
                Text(project.title)
                    .font(.headline.weight(.black))
                Text("\(completed)/\(project.exercises.count) exercises · \(project.estimatedHours) hours")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            TagView(text: project.level, emphasized: true)
        }
        .padding(.horizontal, 16)
        .padding(.top, 8)
    }
}

private struct ProjectSectionPicker: View {
    @Binding var selection: ProjectSection

    var body: some View {
        HStack(spacing: 4) {
            ForEach(ProjectSection.allCases) { section in
                Button {
                    withAnimation(.snappy(duration: 0.24)) { selection = section }
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: section.icon)
                            .font(.caption.bold())
                        Text(section.title)
                            .font(.system(size: 10, weight: .bold, design: .rounded))
                    }
                    .foregroundStyle(selection == section ? .white : .secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 9)
                    .background(
                        selection == section ? AnyShapeStyle(ForgeTheme.emberGradient) : AnyShapeStyle(Color.clear),
                        in: RoundedRectangle(cornerRadius: 11, style: .continuous)
                    )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(Color.secondary.opacity(0.09), in: RoundedRectangle(cornerRadius: 15, style: .continuous))
        .accessibilityElement(children: .contain)
    }
}

private struct ProjectOverviewView: View {
    let project: Project

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 18) {
                ForgeSectionTitle(project.tagline, eyebrow: "Project brief")
                FlowLayout(project.tech) { TagView(text: $0) }

                DetailPanel(title: "What you're building", icon: "cube.transparent") {
                    MarkdownText(project.brief)
                }

                DetailPanel(title: "Environment", icon: "terminal") {
                    VStack(alignment: .leading, spacing: 11) {
                        Text(project.environment.command)
                            .font(.footnote.monospaced().weight(.medium))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(13)
                            .background(ForgeTheme.codeBackground, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                            .foregroundStyle(ForgeTheme.emberLight)
                            .overlay(alignment: .topTrailing) {
                                Image(systemName: "chevron.left.forwardslash.chevron.right")
                                    .font(.caption2)
                                    .foregroundStyle(.white.opacity(0.28))
                                    .padding(10)
                            }
                        Text(project.environment.note)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }

                if let underTheHood = project.underTheHood {
                    DetailPanel(title: "Under the hood", icon: "gearshape.2") {
                        MarkdownText(underTheHood)
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 30)
        }
    }
}

private struct DetailPanel<Content: View>: View {
    let title: String
    let icon: String
    let content: Content

    init(title: String, icon: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.icon = icon
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 13) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .foregroundStyle(ForgeTheme.ember)
                Text(title)
                    .font(.headline.weight(.black))
                Spacer()
                ForgeDivider().frame(width: 42)
            }
            content
        }
        .padding(17)
        .forgePanel(cornerRadius: 20)
    }
}

private struct ExerciseListView: View {
    let project: Project
    let passed: [String: Bool]
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 11) {
                ForEach(Array(project.exercises.enumerated()), id: \.element.id) { index, exercise in
                    NavigationLink {
                        ExerciseView(projectID: project.id, exercise: exercise, initiallyPassed: isPassed(exercise.id))
                    } label: {
                        HStack(spacing: 13) {
                            ZStack {
                                Circle()
                                    .fill(isPassed(exercise.id) ? ForgeTheme.success.opacity(0.14) : ForgeTheme.ember.opacity(0.11))
                                if isPassed(exercise.id) {
                                    Image(systemName: "checkmark")
                                        .font(.caption.bold())
                                        .foregroundStyle(ForgeTheme.success)
                                } else {
                                    Text("\(index + 1)")
                                        .font(.caption.bold().monospacedDigit())
                                        .foregroundStyle(ForgeTheme.ember)
                                }
                            }
                            .frame(width: 40, height: 40)

                            VStack(alignment: .leading, spacing: 5) {
                                Text(exercise.title)
                                    .font(.headline.weight(.bold))
                                    .foregroundStyle(.primary)
                                HStack(spacing: 6) {
                                    Text(exercise.id.uppercased())
                                    Text("·")
                                    Label(exercise.runtime == "local" ? "Local runtime" : "Python", systemImage: "cpu")
                                }
                                .font(.caption2.weight(.semibold))
                                .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption.bold())
                                .foregroundStyle(ForgeTheme.ember)
                        }
                        .padding(15)
                        .forgePanel(cornerRadius: 18)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 30)
        }
        .scrollIndicators(.hidden)
    }

    private func isPassed(_ exerciseID: String) -> Bool {
        passed[exerciseID] == true || model.curriculum?.progress.exercises[exerciseID] == true
    }
}

private struct MilestonesView: View {
    let project: Project
    @State var completed: [Int]
    let didChange: ([Int]) -> Void
    @EnvironmentObject private var model: AppModel
    @State private var pending = Set<Int>()

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 11) {
                ForEach(Array(project.milestones.enumerated()), id: \.offset) { index, milestone in
                    Button { toggle(index) } label: {
                        HStack(alignment: .top, spacing: 13) {
                            ZStack {
                                Circle().fill(completed.contains(index) ? ForgeTheme.success.opacity(0.14) : Color.secondary.opacity(0.10))
                                if pending.contains(index) {
                                    ProgressView().controlSize(.small)
                                } else {
                                    Image(systemName: completed.contains(index) ? "checkmark" : "hammer.fill")
                                        .font(.caption.bold())
                                        .foregroundStyle(completed.contains(index) ? ForgeTheme.success : ForgeTheme.ember)
                                }
                            }
                            .frame(width: 40, height: 40)

                            VStack(alignment: .leading, spacing: 4) {
                                Text("MILESTONE \(index + 1)")
                                    .font(.caption2.bold())
                                    .tracking(0.8)
                                    .foregroundStyle(ForgeTheme.ember)
                                Text(milestone)
                                    .font(.subheadline.weight(.medium))
                                    .foregroundStyle(.primary)
                                    .strikethrough(completed.contains(index))
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                        .padding(15)
                        .forgePanel(cornerRadius: 18)
                    }
                    .buttonStyle(.plain)
                    .disabled(pending.contains(index))
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 30)
        }
        .scrollIndicators(.hidden)
    }

    private func toggle(_ index: Int) {
        let wasDone = completed.contains(index)
        if wasDone { completed.removeAll { $0 == index } } else { completed.append(index) }
        completed.sort()
        pending.insert(index)
        Task {
            defer { pending.remove(index) }
            do {
                completed = try await model.setMilestone(projectID: project.id, index: index, done: !wasDone)
                didChange(completed)
            } catch {
                if wasDone { completed.append(index); completed.sort() } else { completed.removeAll { $0 == index } }
                model.show(error)
            }
        }
    }
}

private struct InterviewView: View {
    let questions: [InterviewQuestion]
    @State private var revealed = Set<String>()

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: 13) {
                ForEach(Array(questions.enumerated()), id: \.element.id) { index, item in
                    VStack(alignment: .leading, spacing: 13) {
                        HStack {
                            Text("QUESTION \(String(format: "%02d", index + 1))")
                                .font(.caption2.bold())
                                .tracking(1.0)
                                .foregroundStyle(ForgeTheme.ember)
                            Spacer()
                            TagView(text: item.difficulty, emphasized: true)
                        }
                        Text(item.question)
                            .font(.headline.weight(.black))

                        FlowLayout(item.topics) { TagView(text: $0) }

                        if revealed.contains(item.id) {
                            ForgeDivider()
                            Text(item.answer)
                                .font(.body.weight(.semibold))
                            Text(item.explanation)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        } else {
                            Button {
                                withAnimation(.snappy) { _ = revealed.insert(item.id) }
                            } label: {
                                Label("Reveal answer", systemImage: "eye")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                    .padding(17)
                    .forgePanel(cornerRadius: 20)
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 30)
        }
    }
}
