import SwiftUI

@main
struct PlaybookLauncherApp: App {
    // One model and one window for the app: a run writes and restores the checkout's env
    // files, so a second window (or a reopened one with a fresh model) must not start another.
    @State private var viewModel = LauncherViewModel()

    var body: some Scene {
        Window("Playbook Launcher", id: "main") {
            ContentView(viewModel: viewModel)
        }
        .windowResizability(.contentSize)
    }
}
