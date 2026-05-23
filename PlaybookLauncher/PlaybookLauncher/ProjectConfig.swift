import Foundation

/// Per-project fields — filled fresh each time.
/// Maps 1:1 to `.env.project` variables.
struct ProjectConfig: Equatable {
    /// The last segment of the bundle ID (e.g., "test-app").
    /// This is the primary input — repo name and app name derive from it.
    var bundleIDSuffix: String = ""
    var repoName: String = ""
    var appName: String = ""
    var minimumIOS: String = "26.0"
    var primarySim: String = "iPhone 17 Pro"

    var isComplete: Bool {
        !bundleIDSuffix.isEmpty && !repoName.isEmpty && !appName.isEmpty
    }
}
