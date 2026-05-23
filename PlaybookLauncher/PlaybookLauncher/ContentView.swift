import SwiftUI

struct ContentView: View {
    @State private var viewModel = LauncherViewModel()
    @State private var showLog = false
    @State private var editingIdentity = false

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

            FormField("App Name", text: $viewModel.project.appName, prompt: "MyApp")
                .onChange(of: viewModel.project.appName) {
                    viewModel.autoFillDerivedFields()
                }

            FormField("Bundle ID", text: $viewModel.project.bundleID, prompt: viewModel.derivedBundleID.isEmpty ? "com.example.myapp" : viewModel.derivedBundleID)

            FormField("Repo Name", text: $viewModel.project.repoName, prompt: viewModel.derivedRepoName.isEmpty ? "myapp" : viewModel.derivedRepoName)

            HStack(spacing: 16) {
                FormField("Min iOS", text: $viewModel.project.minimumIOS, prompt: "26.0")
                    .frame(maxWidth: 120)
                FormField("Simulator", text: $viewModel.project.primarySim, prompt: "iPhone 17 Pro")
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
