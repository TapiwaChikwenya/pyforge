import SwiftUI

struct ServerSettingsView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var address = ""
    @State private var isTesting = false
    @State private var status: TestStatus?

    var body: some View {
        NavigationStack {
            ZStack {
                ForgeBackground()

                ScrollView {
                    VStack(spacing: 18) {
                        connectionHero
                        serverPanel

                        if let status {
                            statusPanel(status)
                                .transition(.move(edge: .top).combined(with: .opacity))
                        }

                        phonePanel
                        supportPanel
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 10)
                    .padding(.bottom, 32)
                }
                .scrollDismissesKeyboard(.interactively)
                .scrollIndicators(.hidden)
            }
            .navigationTitle("Server")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                        .fontWeight(.bold)
                }
            }
            .onAppear { address = model.serverURLString }
        }
    }

    private var connectionHero: some View {
        HStack(spacing: 14) {
            Image("BrandMark")
                .resizable()
                .scaledToFill()
                .frame(width: 60, height: 60)
                .clipShape(RoundedRectangle(cornerRadius: 17, style: .continuous))
                .shadow(color: ForgeTheme.ember.opacity(0.24), radius: 14, y: 6)

            VStack(alignment: .leading, spacing: 4) {
                Text("Your local forge")
                    .font(.title2.weight(.black))
                Text("Connect the app to PyForge running on your Mac.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer(minLength: 0)
        }
        .padding(.vertical, 4)
    }

    private var serverPanel: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("SERVER ADDRESS", systemImage: "network")
                .font(.caption.bold())
                .tracking(0.9)
                .foregroundStyle(ForgeTheme.ember)

            HStack(spacing: 10) {
                Image(systemName: "link")
                    .foregroundStyle(ForgeTheme.steel)
                TextField("http://my-mac.local:8000", text: $address)
                    .keyboardType(.URL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .font(.footnote.monospaced())
                    .submitLabel(.go)
                    .onSubmit { Task { await testAndSave() } }
            }
            .padding(14)
            .background(Color.secondary.opacity(0.08), in: RoundedRectangle(cornerRadius: 13, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .stroke(ForgeTheme.ember.opacity(0.18), lineWidth: 1)
            }

            Button {
                Task { await testAndSave() }
            } label: {
                HStack(spacing: 9) {
                    if isTesting {
                        ProgressView().tint(.white)
                    } else {
                        Image(systemName: "bolt.horizontal.circle.fill")
                    }
                    Text(isTesting ? "Testing connection…" : "Test & Save Connection")
                        .fontWeight(.black)
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(ForgeTheme.emberGradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                .shadow(color: ForgeTheme.ember.opacity(0.24), radius: 12, y: 6)
            }
            .buttonStyle(.plain)
            .disabled(isTesting || address.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .opacity(isTesting || address.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? 0.55 : 1)
        }
        .padding(17)
        .forgePanel(cornerRadius: 22)
    }

    private func statusPanel(_ status: TestStatus) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: status.isSuccess ? "checkmark.seal.fill" : "exclamationmark.octagon.fill")
                .font(.title2)
                .foregroundStyle(status.isSuccess ? ForgeTheme.success : .red)
            VStack(alignment: .leading, spacing: 3) {
                Text(status.isSuccess ? "Forge online" : "Connection failed")
                    .font(.headline.weight(.black))
                Text(status.message)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer(minLength: 0)
        }
        .padding(16)
        .background(
            (status.isSuccess ? ForgeTheme.success : Color.red).opacity(0.10),
            in: RoundedRectangle(cornerRadius: 18, style: .continuous)
        )
        .overlay {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke((status.isSuccess ? ForgeTheme.success : Color.red).opacity(0.22), lineWidth: 1)
        }
    }

    private var phonePanel: some View {
        VStack(alignment: .leading, spacing: 15) {
            ForgeSectionTitle("Connect your iPhone", eyebrow: "Four quick steps")

            SetupStep(number: 1, title: "Start the forge", detail: "Run docker compose up -d --build on your Mac.", icon: "shippingbox.fill")
            SetupStep(number: 2, title: "Share trusted Wi-Fi", detail: "Keep your Mac and iPhone on the same network.", icon: "wifi")
            SetupStep(number: 3, title: "Use your Mac hostname", detail: "Try http://my-mac.local:8000. The Simulator can use 127.0.0.1.", icon: "desktopcomputer")
            SetupStep(number: 4, title: "Keep it private", detail: "Local mode runs code and is intended for your own trusted machine.", icon: "lock.shield.fill")
        }
        .padding(17)
        .forgePanel(cornerRadius: 22)
    }

    private var supportPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("CURRENT SUPPORT")
                .font(.caption.bold())
                .tracking(0.9)
                .foregroundStyle(ForgeTheme.ember)
            SupportRow(title: "Local mode", detail: "Curriculum, code runs & progress", available: true)
            SupportRow(title: "Hosted mode", detail: "Curriculum browsing", available: false)
        }
        .padding(17)
        .forgePanel(cornerRadius: 22)
    }

    private func testAndSave() async {
        isTesting = true
        status = nil
        defer { isTesting = false }
        do {
            let health = try await model.testAndSaveServer(address)
            address = model.serverURLString
            withAnimation(.snappy) {
                status = TestStatus(isSuccess: true, message: "Connected to \(health.mode.rawValue) mode with \(health.projects) projects.")
            }
        } catch {
            withAnimation(.snappy) {
                status = TestStatus(isSuccess: false, message: error.localizedDescription)
            }
        }
    }
}

private struct SetupStep: View {
    let number: Int
    let title: String
    let detail: String
    let icon: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle().fill(ForgeTheme.ember.opacity(0.12))
                Text("\(number)")
                    .font(.caption.bold().monospacedDigit())
                    .foregroundStyle(ForgeTheme.ember)
            }
            .frame(width: 32, height: 32)

            VStack(alignment: .leading, spacing: 2) {
                Label(title, systemImage: icon)
                    .font(.subheadline.weight(.bold))
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

private struct SupportRow: View {
    let title: String
    let detail: String
    let available: Bool

    var body: some View {
        HStack(spacing: 11) {
            Image(systemName: available ? "checkmark.circle.fill" : "info.circle.fill")
                .foregroundStyle(available ? ForgeTheme.success : ForgeTheme.steel)
            VStack(alignment: .leading, spacing: 1) {
                Text(title).font(.subheadline.weight(.bold))
                Text(detail).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Text(available ? "FULL" : "VIEW")
                .font(.system(size: 9, weight: .black, design: .rounded))
                .tracking(0.6)
                .foregroundStyle(available ? ForgeTheme.success : ForgeTheme.steel)
        }
    }
}

private struct TestStatus {
    let isSuccess: Bool
    let message: String
}
