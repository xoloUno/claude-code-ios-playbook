import Foundation

/// Developer identity fields — filled once, persisted in UserDefaults.
/// `teamID` and `org` map to the `.env.playbook` variables bootstrap.sh reads; the domain
/// only derives the bundle ID prefix.
struct IdentityConfig: Codable, Equatable {
    var teamID: String = ""
    var org: String = ""
    var developerDomain: String = ""

    var isComplete: Bool {
        !teamID.isEmpty && !org.isEmpty && !developerDomain.isEmpty
    }
}
