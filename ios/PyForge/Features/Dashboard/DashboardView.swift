import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 26) {
                ForgeHeroCard(
                    progress: model.overallProgress,
                    completed: model.completedExercises,
                    total: model.totalExercises
                )

                if let firstHour = model.curriculum?.firstHour,
                   let project = model.curriculum?.projects.first(where: { $0.id == firstHour.projectID }) {
                    NavigationLink {
                        FirstHourExerciseDestination(summary: project, exerciseID: firstHour.exerciseID)
                    } label: {
                        FirstHourCard(firstHour: firstHour)
                    }
                    .buttonStyle(.plain)
                }

                ForEach(Array((model.curriculum?.stages ?? []).enumerated()), id: \.element.id) { index, stage in
                    VStack(alignment: .leading, spacing: 12) {
                        StageHeader(stage: stage, index: index + 1)

                        ForEach(projects(in: stage)) { project in
                            NavigationLink {
                                ProjectDetailView(summary: project)
                            } label: {
                                ProjectRow(project: project)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 10)
            .padding(.bottom, 36)
        }
        .scrollIndicators(.hidden)
        .refreshable { await model.refresh() }
        .overlay(alignment: .bottom) {
            if case .failed = model.connectionState, model.curriculum != nil {
                Label("Refresh failed · showing current progress", systemImage: "wifi.exclamationmark")
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(.ultraThinMaterial, in: Capsule())
                    .overlay { Capsule().stroke(Color.secondary.opacity(0.12)) }
                    .padding()
            }
        }
    }

    private func projects(in stage: LearningStage) -> [ProjectSummary] {
        let projects = model.curriculum?.projects ?? []
        return stage.projectIDs.compactMap { id in projects.first { $0.id == id } }
    }
}

private struct ForgeHeroCard: View {
    let progress: Double
    let completed: Int
    let total: Int

    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            ForgeTheme.midnightGradient

            Circle()
                .fill(ForgeTheme.ember.opacity(0.28))
                .frame(width: 170, height: 170)
                .blur(radius: 55)
                .offset(x: 75, y: 80)

            Image("BrandMark")
                .resizable()
                .scaledToFill()
                .frame(width: 126, height: 126)
                .clipShape(RoundedRectangle(cornerRadius: 29, style: .continuous))
                .opacity(0.20)
                .offset(x: 32, y: 34)

            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top, spacing: 16) {
                    VStack(alignment: .leading, spacing: 7) {
                        Label("YOUR LEARNING FORGE", systemImage: "sparkles")
                            .font(.caption2.bold())
                            .tracking(1.2)
                            .foregroundStyle(ForgeTheme.emberLight)
                        Text("Build systems.\nProve the skills.")
                            .font(.system(.title, design: .rounded, weight: .black))
                            .foregroundStyle(.white)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    Spacer(minLength: 8)
                    ProgressRing(progress: progress, size: 72)
                }

                HStack(spacing: 7) {
                    ForEach(["PY", "SQL", "SPARK", "AI"], id: \.self) { item in
                        Text(item)
                            .font(.system(size: 9, weight: .black, design: .rounded))
                            .tracking(0.7)
                            .foregroundStyle(.white.opacity(0.78))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(Color.white.opacity(0.075), in: Capsule())
                    }
                }

                HStack {
                    Text("\(completed) forged")
                        .foregroundStyle(.white)
                    Text("·")
                    Text("\(max(total - completed, 0)) ahead")
                }
                .font(.caption.weight(.semibold))
                .foregroundStyle(.white.opacity(0.62))
            }
            .padding(22)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .clipShape(RoundedRectangle(cornerRadius: 28, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .stroke(
                    LinearGradient(
                        colors: [Color.white.opacity(0.22), ForgeTheme.ember.opacity(0.18), .clear],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1
                )
        }
        .shadow(color: ForgeTheme.midnight.opacity(0.28), radius: 24, y: 14)
    }
}

private struct StageHeader: View {
    let stage: LearningStage
    let index: Int

    private var cleanTitle: String {
        stage.title.components(separatedBy: " · ").last ?? stage.title
    }

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 11, style: .continuous)
                    .fill(ForgeTheme.midnightGradient)
                Text(String(format: "%02d", index))
                    .font(.caption.bold().monospacedDigit())
                    .foregroundStyle(ForgeTheme.emberLight)
            }
            .frame(width: 42, height: 38)

            VStack(alignment: .leading, spacing: 2) {
                Text("STAGE \(index)")
                    .font(.system(size: 9, weight: .bold, design: .rounded))
                    .tracking(1.3)
                    .foregroundStyle(ForgeTheme.ember)
                Text(cleanTitle)
                    .font(.headline.weight(.black))
            }

            Spacer()
            ForgeDivider().frame(width: 48)
        }
        .padding(.top, 4)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(.isHeader)
    }
}

private struct ProjectRow: View {
    let project: ProjectSummary

    private var progress: Double {
        guard project.exercisesTotal > 0 else { return 0 }
        return Double(project.exercisesDone) / Double(project.exercisesTotal)
    }

    var body: some View {
        HStack(spacing: 14) {
            ZStack {
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .fill(project.exercisesDone == project.exercisesTotal ? ForgeTheme.success.opacity(0.13) : ForgeTheme.ember.opacity(0.11))
                Text(String(format: "%02d", project.num))
                    .font(.system(.subheadline, design: .monospaced, weight: .black))
                    .foregroundStyle(project.exercisesDone == project.exercisesTotal ? ForgeTheme.success : ForgeTheme.ember)
            }
            .frame(width: 48, height: 54)

            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    Text(project.title)
                        .font(.headline.weight(.bold))
                        .lineLimit(1)
                    Spacer()
                    Text("\(project.estimatedHours)h")
                        .font(.caption2.bold().monospacedDigit())
                        .foregroundStyle(.secondary)
                    Image(systemName: "chevron.right")
                        .font(.caption2.bold())
                        .foregroundStyle(ForgeTheme.ember)
                }

                Text(project.tagline)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)

                HStack(spacing: 10) {
                    ForgeProgressBar(progress: progress, complete: progress == 1)
                    Text("\(project.exercisesDone)/\(project.exercisesTotal)")
                        .font(.caption2.bold().monospacedDigit())
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(14)
        .forgePanel(cornerRadius: 18)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
    }
}

private struct ForgeProgressBar: View {
    let progress: Double
    let complete: Bool

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                Capsule().fill(Color.secondary.opacity(0.13))
                Capsule()
                    .fill(complete ? AnyShapeStyle(ForgeTheme.success) : AnyShapeStyle(ForgeTheme.emberGradient))
                    .frame(width: max(5, proxy.size.width * max(0, min(progress, 1))))
            }
        }
        .frame(height: 5)
        .accessibilityHidden(true)
    }
}

private struct FirstHourCard: View {
    let firstHour: FirstHour

    var body: some View {
        HStack(spacing: 15) {
            ZStack {
                Circle().fill(ForgeTheme.emberGradient)
                Image(systemName: "flame.fill")
                    .font(.title3.bold())
                    .foregroundStyle(.white)
            }
            .frame(width: 48, height: 48)
            .shadow(color: ForgeTheme.ember.opacity(0.30), radius: 12, y: 6)

            VStack(alignment: .leading, spacing: 5) {
                Text("YOUR NEXT STRIKE")
                    .font(.caption2.bold())
                    .tracking(1.15)
                    .foregroundStyle(ForgeTheme.ember)
                Text(firstHour.title)
                    .font(.headline.weight(.black))
                Text("\(firstHour.estimatedMinutes) min · \(firstHour.blurb)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            Spacer(minLength: 0)
            Image(systemName: "arrow.up.right")
                .font(.caption.bold())
                .foregroundStyle(ForgeTheme.ember)
        }
        .padding(16)
        .forgePanel(cornerRadius: 20)
    }
}

private struct FirstHourExerciseDestination: View {
    let summary: ProjectSummary
    let exerciseID: String

    @EnvironmentObject private var model: AppModel
    @State private var response: ProjectResponse?
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            ForgeBackground()
            Group {
                if let response,
                   let exercise = response.project.exercises.first(where: { $0.id == exerciseID }) {
                    ExerciseView(
                        projectID: response.project.id,
                        exercise: exercise,
                        initiallyPassed: response.exercisesPassed[exerciseID] == true
                    )
                } else if let errorMessage {
                    ContentUnavailableView(
                        "Could not load your first exercise",
                        systemImage: "exclamationmark.triangle",
                        description: Text(errorMessage)
                    )
                } else {
                    ProgressView("Preparing your first exercise…")
                }
            }
        }
        .task {
            do {
                response = try await model.loadProject(id: summary.id)
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}
