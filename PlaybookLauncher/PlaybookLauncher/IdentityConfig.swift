import Foundation

/// Developer identity fields — filled once, persisted in UserDefaults.
/// Maps 1:1 to `.env.playbook` variables.
struct IdentityConfig: Codable, Equatable {
    var teamID: String = ""
    var org: String = ""
    var developerName: String = ""
    var developerEmail: String = ""
    var developerDomain: String = ""
    var ascKeyID: String = ""
    var ascIssuerID: String = ""

    var isComplete: Bool {
        !teamID.isEmpty && !org.isEmpty && !developerName.isEmpty
            && !developerEmail.isEmpty && !developerDomain.isEmpty
            && !ascKeyID.isEmpty && !ascIssuerID.isEmpty
    }
}
