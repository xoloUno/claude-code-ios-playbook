import Foundation
import Observation

@Observable
@MainActor
final class LauncherViewModel {
    // MARK: - Identity (persisted)

    var identity = IdentityConfig()

    // MARK: - Project (per-run)

    var project = ProjectConfig()

    // MARK: - Derived fields

    /// Reverse-domain prefix from the identity's domain (e.g., "uno.xolo").
    var bundleIDPrefix: String {
        guard !identity.developerDomain.isEmpty else { return "" }
        return identity.developerDomain
            .split(separator: ".")
            .reversed()
            .joined(separator: ".")
    }

    /// Full bundle ID = prefix + suffix (e.g., "uno.xolo.test-app").
    var fullBundleID: String {
        guard !bundleIDPrefix.isEmpty, !project.bundleIDSuffix.isEmpty else { return "" }
        return bundleIDPrefix + "." + project.bundleIDSuffix
    }

    /// PascalCase app name from the suffix (e.g., "test-app" → "TestApp").
    static func pascalCase(from identifier: String) -> String {
        identifier
            .split(omittingEmptySubsequences: true) { $0 == "-" || $0 == " " || $0 == "_" }
            .map { $0.prefix(1).uppercased() + $0.dropFirst().lowercased() }
            .joined()
    }

    // MARK: - Picker options

    static let minimumIOSOptions = ["26.0", "18.0", "17.0", "16.0"]

    var availableSimulators: [String] = []

    // MARK: - Bootstrap execution state

    var isRunning = false
    var logOutput = ""
    var didFinish = false
    var didSucceed = false

    // MARK: - Playbook path (persisted)

    var playbookPath: String = ""

    var isPlaybookValid: Bool {
        !playbookPath.isEmpty
            && FileManager.default.fileExists(atPath: playbookPath + "/bootstrap.sh")
    }

    var canCreate: Bool {
        identity.isComplete && project.isComplete && isPlaybookValid && !isRunning
    }

    // MARK: - Init

    private static let playbookPathKey = "PlaybookLauncher.playbookPath"

    init() {
        if let saved = UserDefaults.standard.string(forKey: Self.playbookPathKey),
           FileManager.default.fileExists(atPath: saved + "/bootstrap.sh")
        {
            playbookPath = saved
        }

        loadIdentity()
        loadAvailableSimulators()
    }

    func savePlaybookPath() {
        UserDefaults.standard.set(playbookPath, forKey: Self.playbookPathKey)
        // If identity is empty, try seeding from the newly selected playbook's env file
        if !identity.isComplete {
            loadIdentityFromEnvFile()
        }
    }

    // MARK: - Persistence

    private static let identityKey = "PlaybookLauncher.identity"

    func loadIdentity() {
        guard let data = UserDefaults.standard.data(forKey: Self.identityKey),
              let saved = try? JSONDecoder().decode(IdentityConfig.self, from: data)
        else {
            loadIdentityFromEnvFile()
            return
        }
        identity = saved
    }

    func saveIdentity() {
        guard let data = try? JSONEncoder().encode(identity) else { return }
        UserDefaults.standard.set(data, forKey: Self.identityKey)
    }

    /// Seed identity from existing .env.playbook if present and UserDefaults is empty.
    private func loadIdentityFromEnvFile() {
        let envPath = playbookPath + "/.env.playbook"
        guard let contents = try? String(contentsOfFile: envPath, encoding: .utf8) else { return }

        let pairs = parseEnvFile(contents)
        if let v = pairs["TEAM_ID"], v != "YOUR_TEAM_ID" { identity.teamID = v }
        if let v = pairs["ORG"], v != "YourGitHubOrg" { identity.org = v }
        if let v = pairs["DEVELOPER_NAME"], v != "Your Name" { identity.developerName = v }
        if let v = pairs["DEVELOPER_EMAIL"], v != "you@example.com" { identity.developerEmail = v }
        if let v = pairs["DEVELOPER_DOMAIN"], v != "example.com" { identity.developerDomain = v }
        if let v = pairs["ASC_KEY_ID"], v != "YOUR_ASC_KEY_ID" { identity.ascKeyID = v }
        if let v = pairs["ASC_ISSUER_ID"], v != "YOUR_ASC_ISSUER_ID" { identity.ascIssuerID = v }

        if identity != IdentityConfig() {
            saveIdentity()
        }
    }

    private func parseEnvFile(_ contents: String) -> [String: String] {
        var result: [String: String] = [:]
        for line in contents.components(separatedBy: .newlines) {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard !trimmed.isEmpty, !trimmed.hasPrefix("#") else { continue }
            let parts = trimmed.split(separator: "=", maxSplits: 1)
            guard parts.count == 2 else { continue }
            let key = String(parts[0]).trimmingCharacters(in: .whitespaces)
            var value = String(parts[1]).trimmingCharacters(in: .whitespaces)
            // Strip surrounding quotes
            if (value.hasPrefix("\"") && value.hasSuffix("\""))
                || (value.hasPrefix("'") && value.hasSuffix("'"))
            {
                value = String(value.dropFirst().dropLast())
            }
            result[key] = value
        }
        return result
    }

    // MARK: - Auto-fill helpers

    /// Called on every keystroke in the bundle ID suffix field (primary input).
    /// Derives repo name and app name from the suffix.
    func autoFillFromSuffix() {
        project.repoName = project.bundleIDSuffix
        project.appName = Self.pascalCase(from: project.bundleIDSuffix)
    }

    /// Strip characters that aren't valid in a Swift type name.
    /// Letters and numbers only, first character forced uppercase.
    func sanitizeAppName() {
        let filtered = project.appName.filter { $0.isLetter || $0.isNumber }
        let capitalized = filtered.prefix(1).uppercased() + filtered.dropFirst()
        if capitalized != project.appName {
            project.appName = capitalized
        }
    }

    /// Live: force lowercase, strip everything except alphanumeric + hyphens.
    func sanitizeBundleIDSuffix() {
        let lowered = project.bundleIDSuffix.lowercased()
        let filtered = lowered.filter { $0.isLetter || $0.isNumber || $0 == "-" }
        if filtered != project.bundleIDSuffix {
            project.bundleIDSuffix = filtered
        }
    }

    /// On blur: trim leading/trailing hyphens.
    func commitBundleIDSuffix() {
        let trimmed = project.bundleIDSuffix.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
        if trimmed != project.bundleIDSuffix {
            project.bundleIDSuffix = trimmed
        }
    }

    /// Live: strip everything except alphanumeric, hyphens, dots, underscores.
    func sanitizeRepoName() {
        let filtered = project.repoName.filter { $0.isLetter || $0.isNumber || $0 == "-" || $0 == "." || $0 == "_" }
        if filtered != project.repoName {
            project.repoName = filtered
        }
    }

    /// On blur: trim leading/trailing hyphens.
    func commitRepoName() {
        let trimmed = project.repoName.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
        if trimmed != project.repoName {
            project.repoName = trimmed
        }
    }

    /// Query xcrun simctl for available iOS simulators.
    func loadAvailableSimulators() {
        Task.detached {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/xcrun")
            process.arguments = ["simctl", "list", "devices", "available", "-j"]

            let pipe = Pipe()
            process.standardOutput = pipe
            process.standardError = Pipe()

            do {
                try process.run()
                process.waitUntilExit()
            } catch {
                return
            }

            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let devicesMap = json["devices"] as? [String: [[String: Any]]]
            else { return }

            var names: [String] = []
            for (runtime, devices) in devicesMap {
                // Only iOS simulators
                guard runtime.contains("iOS") || runtime.contains("iphonesimulator") else { continue }
                for device in devices {
                    if let name = device["name"] as? String,
                       let isAvailable = device["isAvailable"] as? Bool,
                       isAvailable
                    {
                        if !names.contains(name) {
                            names.append(name)
                        }
                    }
                }
            }

            let sorted = names.sorted()
            await MainActor.run { [sorted] in
                self.availableSimulators = sorted
            }
        }
    }

    // MARK: - Bootstrap execution

    func runBootstrap() {
        guard canCreate else { return }

        isRunning = true
        logOutput = ""
        didFinish = false
        didSucceed = false

        saveIdentity()

        let envPlaybook = buildEnvPlaybook()
        let envProject = buildEnvProject()
        let scriptPath = playbookPath + "/bootstrap.sh"
        let playbookDir = playbookPath

        Task.detached { [weak self] in
            await self?.executeBootstrap(
                scriptPath: scriptPath,
                playbookDir: playbookDir,
                envPlaybook: envPlaybook,
                envProject: envProject
            )
        }
    }

    private func buildEnvPlaybook() -> String {
        """
        TEAM_ID="\(identity.teamID)"
        ORG="\(identity.org)"
        DEVELOPER_NAME="\(identity.developerName)"
        DEVELOPER_EMAIL="\(identity.developerEmail)"
        DEVELOPER_DOMAIN="\(identity.developerDomain)"
        ASC_KEY_ID="\(identity.ascKeyID)"
        ASC_ISSUER_ID="\(identity.ascIssuerID)"
        """
    }

    private func buildEnvProject() -> String {
        """
        APP_NAME="\(project.appName)"
        BUNDLE_ID="\(fullBundleID)"
        REPO_NAME="\(project.repoName)"
        MINIMUM_IOS="\(project.minimumIOS)"
        PRIMARY_SIM="\(project.primarySim)"
        """
    }

    private func executeBootstrap(
        scriptPath: String,
        playbookDir: String,
        envPlaybook: String,
        envProject: String
    ) async {
        // Write temporary env files
        let envPlaybookPath = playbookDir + "/.env.playbook"
        let envProjectPath = playbookDir + "/.env.project"

        // Preserve existing .env.playbook if present
        let hadExistingPlaybookEnv = FileManager.default.fileExists(atPath: envPlaybookPath)
        let existingPlaybookBackup = hadExistingPlaybookEnv
            ? try? String(contentsOfFile: envPlaybookPath, encoding: .utf8)
            : nil

        let hadExistingProjectEnv = FileManager.default.fileExists(atPath: envProjectPath)

        do {
            try envPlaybook.write(toFile: envPlaybookPath, atomically: true, encoding: .utf8)
            try envProject.write(toFile: envProjectPath, atomically: true, encoding: .utf8)
        } catch {
            await MainActor.run {
                logOutput += "Failed to write env files: \(error.localizedDescription)\n"
                isRunning = false
                didFinish = true
                didSucceed = false
            }
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [scriptPath]
        process.currentDirectoryURL = URL(fileURLWithPath: playbookDir)

        // Inherit PATH so xcodegen, gh, etc. are found
        var env = ProcessInfo.processInfo.environment
        env["TERM"] = "dumb"
        process.environment = env

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            Task { @MainActor [weak self] in
                self?.logOutput += text
            }
        }

        do {
            try process.run()
            process.waitUntilExit()
        } catch {
            await MainActor.run {
                logOutput += "Failed to launch bootstrap.sh: \(error.localizedDescription)\n"
            }
        }

        pipe.fileHandleForReading.readabilityHandler = nil

        let success = process.terminationStatus == 0

        // Restore or clean up env files
        if let backup = existingPlaybookBackup {
            try? backup.write(toFile: envPlaybookPath, atomically: true, encoding: .utf8)
        }
        if !hadExistingProjectEnv {
            try? FileManager.default.removeItem(atPath: envProjectPath)
        }

        await MainActor.run {
            isRunning = false
            didFinish = true
            didSucceed = success
        }
    }
}
