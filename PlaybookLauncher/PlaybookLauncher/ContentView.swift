import SwiftUI

struct ContentView: View {
    @State private var viewModel = LauncherViewModel()
    @State private var showLog = false
    @State private var editingIdentity = false
    @FocusState private var focusedField: ProjectField?

    enum ProjectField: Hashable {
        case repoName, bundleIDSuffix, appName
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    header
                    playbookPathSection
                    identitySection
                    Divider()
                    projectSection
                }
                .padding(24)
            }

            Divider()
            bottomBar
        }
        .frame(minWidth: 520, maxWidth: 520, minHeight: 580)
        .sheet(isPresented: $showLog) {
            LogView(viewModel: viewModel, isPresented: $showLog)
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: 12) {
            Image(systemName: "hammer.fill")
                .font(.system(size: 28))
                .foregroundStyle(.tint)
            VStack(alignment: .leading, spacing: 2) {
                Text("Playbook Launcher")
                    .font(.title2.bold())
                Text("Create a new iOS project from the playbook")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
    }

    // MARK: - Playbook Path

    private var playbookPathSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Playbook Location")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                TextField(
                    "Playbook path",
                    text: $viewModel.playbookPath,
                    prompt: Text("/path/to/playbook")
                )
                .textFieldStyle(.roundedBorder)
                .font(.system(.body, design: .monospaced))
                .onChange(of: viewModel.playbookPath) {
                    viewModel.savePlaybookPath()
                }

                Button("Browse\u{2026}") {
                    let panel = NSOpenPanel()
                    panel.canChooseDirectories = true
                    panel.canChooseFiles = false
                    panel.allowsMultipleSelection = false
                    panel.message = "Select the playbook directory (contains bootstrap.sh)"
                    if panel.runModal() == .OK, let url = panel.url {
                        viewModel.playbookPath = url.path(percentEncoded: false)
                        viewModel.savePlaybookPath()
                    }
                }
            }

            if !viewModel.playbookPath.isEmpty {
                if viewModel.isPlaybookValid {
                    Label("bootstrap.sh found", systemImage: "checkmark.circle.fill")
                        .font(.caption)
                        .foregroundStyle(.green)
                } else {
                    Label("bootstrap.sh not found at this path", systemImage: "xmark.circle.fill")
                        .font(.caption)
                        .foregroundStyle(.red)
                }
            }
        }
    }

    // MARK: - Identity

    private var identitySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Developer Identity", systemImage: "person.crop.circle")
                .font(.headline)

            if viewModel.identity.isComplete && !editingIdentity {
                completedIdentitySummary
            } else {
                identityFields
            }
        }
    }

    private var completedIdentitySummary: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Label(viewModel.identity.developerName, systemImage: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                    .font(.subheadline)
                Spacer()
                Button("Edit") {
                    editingIdentity = true
                }
            }
            Text("\(viewModel.identity.org) \u{2022} \(viewModel.identity.developerDomain)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .background(.fill.quaternary, in: RoundedRectangle(cornerRadius: 8))
    }

    @ViewBuilder
    private var identityFields: some View {
        Group {
            FormField("Team ID", text: $viewModel.identity.teamID, prompt: "10-char alphanumeric")
            FormField("GitHub Org / Username", text: $viewModel.identity.org, prompt: "xoloUno")
            FormField("Developer Name", text: $viewModel.identity.developerName, prompt: "Your Name")
            FormField("Developer Email", text: $viewModel.identity.developerEmail, prompt: "you@example.com")
            FormField("Developer Domain", text: $viewModel.identity.developerDomain, prompt: "example.com")
            FormField("ASC Key ID", text: $viewModel.identity.ascKeyID, prompt: "From App Store Connect → Integrations")
            FormField("ASC Issuer ID", text: $viewModel.identity.ascIssuerID, prompt: "From App Store Connect → Integrations")

            if editingIdentity && viewModel.identity.isComplete {
                HStack {
                    Spacer()
                    Button("Done") { editingIdentity = false }
                        .buttonStyle(.bordered)
                }
            }
        }
        .onChange(of: viewModel.identity) {
            viewModel.saveIdentity()
        }
    }

    // MARK: - Project

    private var projectSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("New Project", systemImage: "plus.app")
                .font(.headline)

            // Bundle ID: prefix label + editable suffix (primary input)
            VStack(alignment: .leading, spacing: 4) {
                Text("Bundle ID")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(.secondary)
                HStack(spacing: 0) {
                    if !viewModel.bundleIDPrefix.isEmpty {
                        Text(viewModel.bundleIDPrefix + ".")
                            .font(.system(.body, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .padding(.leading, 6)
                    }
                    TextField(
                        "app identifier",
                        text: $viewModel.project.bundleIDSuffix,
                        prompt: Text("my-app")
                    )
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
                    .focused($focusedField, equals: .bundleIDSuffix)
                    .onChange(of: viewModel.project.bundleIDSuffix) {
                        viewModel.sanitizeBundleIDSuffix()
                        viewModel.autoFillFromSuffix()
                    }
                }
            }

            FormField("Repo Name", text: $viewModel.project.repoName, prompt: "my-app")
                .focused($focusedField, equals: .repoName)
                .onChange(of: viewModel.project.repoName) {
                    viewModel.sanitizeRepoName()
                }

            FormField("App Name", text: $viewModel.project.appName, prompt: "MyApp")
                .focused($focusedField, equals: .appName)
                .onChange(of: viewModel.project.appName) {
                    viewModel.sanitizeAppName()
                }

            // Trim hyphens when focus leaves a field
            .onChange(of: focusedField) { old, _ in
                if old == .bundleIDSuffix { viewModel.commitBundleIDSuffix() }
                if old == .repoName { viewModel.commitRepoName() }
            }

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Min iOS")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.secondary)
                    Picker("Min iOS", selection: $viewModel.project.minimumIOS) {
                        ForEach(LauncherViewModel.minimumIOSOptions, id: \.self) { version in
                            Text(version).tag(version)
                        }
                    }
                    .labelsHidden()
                }
                .frame(maxWidth: 100)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Simulator")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.secondary)
                    Picker("Simulator", selection: $viewModel.project.primarySim) {
                        ForEach(viewModel.availableSimulators, id: \.self) { sim in
                            Text(sim).tag(sim)
                        }
                    }
                    .labelsHidden()
                }
            }
        }
    }

    // MARK: - Bottom Bar

    private var bottomBar: some View {
        HStack {
            if viewModel.didFinish {
                Label(
                    viewModel.didSucceed ? "Project created" : "Bootstrap failed",
                    systemImage: viewModel.didSucceed ? "checkmark.circle.fill" : "xmark.circle.fill"
                )
                .foregroundStyle(viewModel.didSucceed ? .green : .red)
                .font(.subheadline)

                Button("View Log") { showLog = true }
                    .buttonStyle(.link)
            }

            Spacer()

            Button("Create Project") {
                showLog = true
                viewModel.runBootstrap()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(!viewModel.canCreate)
        }
        .padding(16)
    }
}

// MARK: - Form Field

struct FormField: View {
    let label: String
    @Binding var text: String
    let prompt: String

    init(_ label: String, text: Binding<String>, prompt: String) {
        self.label = label
        self._text = text
        self.prompt = prompt
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)
            TextField(label, text: $text, prompt: Text(prompt))
                .textFieldStyle(.roundedBorder)
        }
    }
}

// MARK: - Log Sheet

struct LogView: View {
    let viewModel: LauncherViewModel
    @Binding var isPresented: Bool

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                if viewModel.isRunning {
                    ProgressView()
                        .controlSize(.small)
                    Text("Running bootstrap.sh\u{2026}")
                        .font(.headline)
                } else if viewModel.didFinish {
                    Image(systemName: viewModel.didSucceed ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundStyle(viewModel.didSucceed ? .green : .red)
                    Text(viewModel.didSucceed ? "Done" : "Failed")
                        .font(.headline)
                } else {
                    Text("Bootstrap Log")
                        .font(.headline)
                }
                Spacer()
                Button("Close") { isPresented = false }
                    .keyboardShortcut(.cancelAction)
            }
            .padding()

            Divider()

            ScrollViewReader { proxy in
                ScrollView {
                    Text(viewModel.logOutput.isEmpty ? "Waiting for output\u{2026}" : viewModel.logOutput)
                        .font(.system(.caption, design: .monospaced))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(12)
                        .textSelection(.enabled)
                        .id("log-bottom")
                }
                .onChange(of: viewModel.logOutput) {
                    proxy.scrollTo("log-bottom", anchor: .bottom)
                }
            }
            .background(.black.opacity(0.03))
        }
        .frame(width: 600, height: 400)
    }
}

#Preview {
    ContentView()
}
