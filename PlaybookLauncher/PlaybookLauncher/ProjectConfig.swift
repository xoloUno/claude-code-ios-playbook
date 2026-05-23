import Foundation

/// Per-project fields — filled fresh each time.
/// Maps 1:1 to `.env.project` variables.
struct ProjectConfig: Equatable {
    var appName: String = ""
    var bundleID: String = ""
    var repoName: String = ""
    var minimumIOS: String = "26.0"
    var primarySim: String = "iPhone 17 Pro"

    var isComplete: Bool {
        !appName.isEmpty && !bundleID.isEmpty && !repoName.isEmpty
    }
}
