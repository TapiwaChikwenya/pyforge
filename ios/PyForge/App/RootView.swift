import SwiftUI

struct RootView: View {
    @EnvironmentObject private var model: AppModel
    @State private var showingSettings = false

    var body: some View {
        NavigationStack {
            ZStack {
                ForgeBackground()
                Group {
                    if model.curriculum == nil {
                        switch model.connectionState {
                        case .failed(let message):
                            ConnectionFailureView(message: message) {
                                Task { await model.refresh() }
                            } settings: {
                                showingSettings = true
                            }
                        default:
                            VStack(spacing: 18) {
                                Image("BrandMark")
                                    .resizable()
                                    .scaledToFill()
                                    .frame(width: 92, height: 92)
                                    .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
                                    .shadow(color: ForgeTheme.ember.opacity(0.3), radius: 24, y: 12)
                                ProgressView()
                                    .tint(ForgeTheme.ember)
                                Text("Heating the forge…")
                                    .font(.headline)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    } else {
                        DashboardView()
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    ForgeWordmark(compact: true)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showingSettings = true } label: {
                        Image(systemName: "server.rack")
                            .font(.subheadline.bold())
                            .frame(width: 34, height: 34)
                            .background(ForgeTheme.ember.opacity(0.12), in: Circle())
                    }
                    .accessibilityLabel("Configure server")
                }
            }
        }
        .sheet(isPresented: $showingSettings) {
            ServerSettingsView()
        }
    }
}

private struct ConnectionFailureView: View {
    let message: String
    let retry: () -> Void
    let settings: () -> Void

    var body: some View {
        VStack(spacing: 18) {
            Image("BrandMark")
                .resizable()
                .scaledToFill()
                .frame(width: 84, height: 84)
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                .shadow(color: ForgeTheme.ember.opacity(0.25), radius: 20, y: 10)
            ForgeSectionTitle("The forge is offline", eyebrow: "Connection needed", detail: message)
                .multilineTextAlignment(.center)
            Button("Try Again", action: retry)
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            Button("Configure Server", action: settings)
                .buttonStyle(.bordered)
        }
        .padding(28)
        .forgePanel(cornerRadius: 26)
        .padding()
    }
}
