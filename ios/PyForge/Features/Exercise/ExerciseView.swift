import SwiftUI

struct ExerciseView: View {
    let projectID: String
    let exercise: Exercise
    let initiallyPassed: Bool

    @EnvironmentObject private var model: AppModel
    @State private var code: String
    @State private var result: RunResponse?
    @State private var isRunning = false
    @State private var visibleHints = 0
    @State private var isPassed: Bool
    @FocusState private var editorFocused: Bool

    init(projectID: String, exercise: Exercise, initiallyPassed: Bool) {
        self.projectID = projectID
        self.exercise = exercise
        self.initiallyPassed = initiallyPassed
        _code = State(initialValue: exercise.starterCode)
        _isPassed = State(initialValue: initiallyPassed)
    }

    var body: some View {
        ZStack {
            ForgeBackground()
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    exerciseHeader

                    ExercisePanel(title: "The challenge", icon: "scope") {
                        MarkdownText(exercise.instructions)
                    }

                    if !exercise.objectives.isEmpty {
                        ExercisePanel(title: "You'll master", icon: "sparkles") {
                            VStack(alignment: .leading, spacing: 10) {
                                ForEach(exercise.objectives, id: \.self) { objective in
                                    HStack(alignment: .top, spacing: 10) {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundStyle(ForgeTheme.ember)
                                        Text(objective)
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                    }
                                }
                            }
                            .font(.subheadline)
                        }
                    }

                    editor
                    runControls

                    if let result { RunResultView(result: result) }
                    hints
                    resources
                }
                .padding(.horizontal, 16)
                .padding(.top, 8)
                .padding(.bottom, 40)
            }
            .scrollIndicators(.hidden)
        }
        .navigationTitle(exercise.title)
        .navigationBarTitleDisplayMode(.inline)
        .sensoryFeedback(.success, trigger: isPassed)
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Button("Insert Tab") { code.append("    ") }
                Spacer()
                Button("Done") { editorFocused = false }
            }
        }
    }

    private var exerciseHeader: some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(isPassed ? AnyShapeStyle(ForgeTheme.success.gradient) : AnyShapeStyle(ForgeTheme.emberGradient))
                Image(systemName: isPassed ? "checkmark.seal.fill" : "hammer.fill")
                    .font(.title3.bold())
                    .foregroundStyle(.white)
            }
            .frame(width: 52, height: 52)
            .shadow(color: (isPassed ? ForgeTheme.success : ForgeTheme.ember).opacity(0.25), radius: 12, y: 6)

            VStack(alignment: .leading, spacing: 3) {
                Text(exercise.id.uppercased())
                    .font(.caption2.bold())
                    .tracking(1.2)
                    .foregroundStyle(isPassed ? ForgeTheme.success : ForgeTheme.ember)
                Text(isPassed ? "Skill forged" : "Ready at the anvil")
                    .font(.headline.weight(.black))
            }
            Spacer()
            TagView(text: exercise.runtime == "local" ? "Local runtime" : "Python", emphasized: true)
        }
    }

    private var editor: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                HStack(spacing: 5) {
                    Circle().fill(ForgeTheme.coral).frame(width: 8, height: 8)
                    Circle().fill(ForgeTheme.emberLight).frame(width: 8, height: 8)
                    Circle().fill(ForgeTheme.success).frame(width: 8, height: 8)
                }
                Text("solution.py")
                    .font(.caption.monospaced().weight(.semibold))
                    .foregroundStyle(.white.opacity(0.72))
                Spacer()
                Text("\(code.components(separatedBy: .newlines).count) lines")
                    .font(.caption2.monospaced())
                    .foregroundStyle(.white.opacity(0.42))
                Button("Reset") { code = exercise.starterCode }
                    .font(.caption2.bold())
                    .foregroundStyle(ForgeTheme.emberLight)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 11)
            .background(Color.white.opacity(0.045))

            Rectangle().fill(Color.white.opacity(0.07)).frame(height: 1)

            TextEditor(text: $code)
                .font(.system(size: 14, weight: .regular, design: .monospaced))
                .autocorrectionDisabled()
                .textInputAutocapitalization(.never)
                .focused($editorFocused)
                .scrollContentBackground(.hidden)
                .padding(10)
                .frame(minHeight: 300)
                .foregroundStyle(Color(red: 0.88, green: 0.91, blue: 0.98))
                .tint(ForgeTheme.emberLight)
                .accessibilityLabel("Python solution editor")
        }
        .background(ForgeTheme.codeBackground, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(editorFocused ? ForgeTheme.ember.opacity(0.80) : Color.white.opacity(0.09), lineWidth: editorFocused ? 1.5 : 1)
        }
        .shadow(color: ForgeTheme.midnight.opacity(0.22), radius: 18, y: 10)
    }

    @ViewBuilder
    private var runControls: some View {
        if model.curriculum?.mode == .hosted {
            ExercisePanel(title: "Local forge required", icon: "lock.shield") {
                Text("This server is in hosted mode, where exercise execution is intentionally disabled. Connect to the local PyForge server on your Mac to run checks from the app.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        } else {
            Button {
                Task { await run() }
            } label: {
                HStack(spacing: 10) {
                    if isRunning {
                        ProgressView().tint(.white)
                    } else {
                        Image(systemName: "play.fill")
                    }
                    Text(isRunning ? "Running checks…" : "Run & Check")
                        .font(.headline.weight(.black))
                    Spacer()
                    if !isRunning { Image(systemName: "arrow.right") }
                }
                .foregroundStyle(.white)
                .padding(.horizontal, 18)
                .frame(height: 56)
                .background(ForgeTheme.emberGradient, in: RoundedRectangle(cornerRadius: 17, style: .continuous))
                .shadow(color: ForgeTheme.ember.opacity(0.30), radius: 16, y: 8)
            }
            .buttonStyle(.plain)
            .disabled(isRunning || code.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .opacity(isRunning ? 0.78 : 1)
        }
    }

    @ViewBuilder
    private var hints: some View {
        if !exercise.hints.isEmpty {
            ExercisePanel(title: "Hints", icon: "lightbulb.max.fill") {
                VStack(alignment: .leading, spacing: 12) {
                    ForEach(Array(exercise.hints.prefix(visibleHints).enumerated()), id: \.offset) { index, hint in
                        HStack(alignment: .top, spacing: 10) {
                            Text("\(index + 1)")
                                .font(.caption.bold().monospacedDigit())
                                .foregroundStyle(.white)
                                .frame(width: 24, height: 24)
                                .background(ForgeTheme.emberGradient, in: Circle())
                            Text(hint)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    if visibleHints < exercise.hints.count {
                        Button(visibleHints == 0 ? "Reveal first hint" : "Reveal another hint") {
                            withAnimation(.snappy) { visibleHints += 1 }
                        }
                        .font(.subheadline.bold())
                    }
                }
                .font(.subheadline)
            }
        }
    }

    @ViewBuilder
    private var resources: some View {
        if !exercise.resources.isEmpty {
            ExercisePanel(title: "Keep learning", icon: "books.vertical.fill") {
                VStack(spacing: 0) {
                    ForEach(Array(exercise.resources.enumerated()), id: \.element.id) { index, resource in
                        if let url = URL(string: resource.url) {
                            Link(destination: url) {
                                HStack {
                                    Text(resource.title)
                                        .font(.subheadline.weight(.semibold))
                                        .multilineTextAlignment(.leading)
                                    Spacer()
                                    Image(systemName: "arrow.up.right")
                                        .font(.caption.bold())
                                        .foregroundStyle(ForgeTheme.ember)
                                }
                                .padding(.vertical, 11)
                            }
                            if index < exercise.resources.count - 1 { Divider() }
                        }
                    }
                }
            }
        }
    }

    private func run() async {
        editorFocused = false
        isRunning = true
        result = nil
        defer { isRunning = false }
        do {
            let response = try await model.run(projectID: projectID, exercise: exercise, code: code)
            result = response
            isPassed = isPassed || response.passed
        } catch {
            model.show(error)
        }
    }
}

private struct ExercisePanel<Content: View>: View {
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
                Image(systemName: icon).foregroundStyle(ForgeTheme.ember)
                Text(title).font(.headline.weight(.black))
                Spacer()
                ForgeDivider().frame(width: 40)
            }
            content
        }
        .padding(17)
        .forgePanel(cornerRadius: 20)
    }
}

private struct RunResultView: View {
    let result: RunResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label(
                    result.passed ? "All checks passed" : result.timedOut ? "Execution timed out" : "Checks failed",
                    systemImage: result.passed ? "checkmark.seal.fill" : "xmark.octagon.fill"
                )
                .font(.headline.weight(.black))
                .foregroundStyle(result.passed ? ForgeTheme.success : .red)
                Spacer()
                Text(result.passed ? "FORGED" : "REFINE")
                    .font(.caption2.bold())
                    .tracking(1)
                    .foregroundStyle(result.passed ? ForgeTheme.success : .red)
            }

            if !result.output.isEmpty { outputBlock(title: "OUTPUT", text: result.output) }
            if !result.error.isEmpty { outputBlock(title: "ERROR", text: result.error) }
        }
        .padding(17)
        .background((result.passed ? ForgeTheme.success : Color.red).opacity(0.09), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke((result.passed ? ForgeTheme.success : Color.red).opacity(0.18))
        }
        .accessibilityElement(children: .contain)
    }

    private func outputBlock(title: String, text: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption2.bold())
                .tracking(1)
                .foregroundStyle(.secondary)
            Text(text)
                .font(.footnote.monospaced())
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(ForgeTheme.codeBackground, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                .foregroundStyle(.white)
        }
    }
}
