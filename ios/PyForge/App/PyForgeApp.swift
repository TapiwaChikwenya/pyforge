import SwiftUI

@main
struct PyForgeApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .tint(ForgeTheme.accent)
                .fontDesign(.rounded)
                .task { await model.start() }
                .alert(item: $model.presentedError) { error in
                    Alert(title: Text("Something went wrong"), message: Text(error.message))
                }
        }
    }
}
