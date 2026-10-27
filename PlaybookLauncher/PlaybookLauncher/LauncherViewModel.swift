import Foundation
import Observation
import Synchronization

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

    static let minimumIOSOptions = ["27.0", "26.0", "18.0", "17.0", "16.0"]

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
        // Re-save so fields older versions stored (the ASC IDs among them) don't linger.
        saveIdentity()
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
        if let v = pairs["DEVELOPER_DOMAIN"], v != "example.com" { identity.developerDomain = v }

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

    /// Only the identity values bootstrap.sh reads. The ASC IDs come from each project's
    /// `.env.fastlane` and GitHub Secrets, so the launcher doesn't collect them.
    private func buildEnvPlaybook() -> String {
        """
        TEAM_ID=\(Self.shellQuoted(identity.teamID))
        ORG=\(Self.shellQuoted(identity.org))
        """
    }

    private func buildEnvProject() -> String {
        """
        APP_NAME=\(Self.shellQuoted(project.appName))
        BUNDLE_ID=\(Self.shellQuoted(fullBundleID))
        REPO_NAME=\(Self.shellQuoted(project.repoName))
        MINIMUM_IOS=\(Self.shellQuoted(project.minimumIOS))
        PRIMARY_SIM=\(Self.shellQuoted(project.primarySim))
        """
    }

    /// Single-quotes a value for a file bash `source`s, so `"`, `$` and backticks stay literal.
    private static func shellQuoted(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: #"'\''"#) + "'"
    }

    private func executeBootstrap(
        scriptPath: String,
        playbookDir: String,
        envPlaybook: String,
        envProject: String
    ) async {
        let envPlaybookPath = playbookDir + "/.env.playbook"
        let envProjectPath = playbookDir + "/.env.project"

        // Snapshot both env files so the run leaves them as it found them: restored if they
        // existed, removed if they didn't.
        let playbookBackup = try? String(contentsOfFile: envPlaybookPath, encoding: .utf8)
        let projectBackup = try? String(contentsOfFile: envProjectPath, encoding: .utf8)
        for (path, backup) in [(envPlaybookPath, playbookBackup), (envProjectPath, projectBackup)]
        where backup == nil && FileManager.default.fileExists(atPath: path) {
            finish(success: false, log: "Can't read the existing \(path), so it was left untouched.\n")
            return
        }
        defer {
            Self.restore(envPlaybookPath, to: playbookBackup)
            Self.restore(envProjectPath, to: projectBackup)
        }

        do {
            try envPlaybook.write(toFile: envPlaybookPath, atomically: true, encoding: .utf8)
            try envProject.write(toFile: envProjectPath, atomically: true, encoding: .utf8)
        } catch {
            finish(success: false, log: "Failed to write env files: \(error.localizedDescription)\n")
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [scriptPath]
        process.currentDirectoryURL = URL(fileURLWithPath: playbookDir)

        // A GUI app inherits launchd's minimal PATH, not the shell's, so add Homebrew's
        // prefixes (Apple silicon, then Intel) where xcodegen and gh live.
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + (env["PATH"] ?? "/usr/bin:/bin:/usr/sbin:/sbin")
        env["TERM"] = "dumb"
        process.environment = env

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        // Output arrives in arbitrary chunks, so LineBuffer holds back a partial line (and any
        // emoji split between chunks) until it's complete. The stream ends at EOF, once the
        // script and everything it started have closed the pipe, so no tail is lost.
        let (output, outputContinuation) = AsyncStream<String>.makeStream()
        let lines = LineBuffer()
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if data.isEmpty {
                handle.readabilityHandler = nil
                if let rest = lines.flush() { outputContinuation.yield(rest) }
                outputContinuation.finish()
            } else if let text = lines.append(data) {
                outputContinuation.yield(text)
            }
        }

        // Await the exit instead of blocking the main thread in waitUntilExit().
        let (exitStatus, exitContinuation) = AsyncStream<Int32>.makeStream()
        process.terminationHandler = { finished in
            exitContinuation.yield(finished.terminationStatus)
            exitContinuation.finish()
        }

        do {
            try process.run()
        } catch {
            // Never launched: there's no output to wait for and no exit status to read.
            pipe.fileHandleForReading.readabilityHandler = nil
            finish(success: false, log: "Failed to launch bootstrap.sh: \(error.localizedDescription)\n")
            return
        }

        for await text in output {
            logOutput += text
        }
        var exit = exitStatus.makeAsyncIterator()
        let status = await exit.next()
        finish(success: status == 0)
    }

    private func finish(success: Bool, log: String = "") {
        logOutput += log
        isRunning = false
        didFinish = true
        didSucceed = success
    }

    private static func restore(_ path: String, to backup: String?) {
        if let backup {
            try? backup.write(toFile: path, atomically: true, encoding: .utf8)
        } else {
            try? FileManager.default.removeItem(atPath: path)
        }
    }
}

/// Collects a process's output and releases it a whole line at a time, so a multi-byte
/// character split across two reads is decoded once it's complete instead of dropped.
private final class LineBuffer: Sendable {
    private let pending = Mutex(Data())

    /// Adds `data` and returns every complete line so far, or nil if there's none yet.
    func append(_ data: Data) -> String? {
        pending.withLock { buffer in
            buffer.append(data)
            guard let newline = buffer.lastIndex(of: UInt8(ascii: "\n")) else { return nil }
            let text = String(decoding: buffer[...newline], as: UTF8.self)
            buffer.removeSubrange(...newline)
            return text
        }
    }

    /// Returns what's left after the last newline, or nil if nothing is.
    func flush() -> String? {
        pending.withLock { buffer in
            guard !buffer.isEmpty else { return nil }
            defer { buffer.removeAll() }
            return String(decoding: buffer, as: UTF8.self)
        }
    }
}
