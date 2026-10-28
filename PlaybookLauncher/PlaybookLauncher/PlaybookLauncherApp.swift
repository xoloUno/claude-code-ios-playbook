import SwiftUI

@main
struct PlaybookLauncherApp: App {
    // One model for every window: a run writes and restores the checkout's env files, so its
    // isRunning flag must disable Create in any other window, and in one opened mid-run.
    // WindowGroup rather than a single Window, which would quit the app (and abandon the
    // restore) when it's closed during a run.
    @State private var viewModel = LauncherViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView(viewModel: viewModel)
        }
        .windowResizability(.contentSize)
    }
}
