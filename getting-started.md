# Getting Started — Step by Step

A plain-language walkthrough for creating a new iOS project using the playbook.
No terminal experience assumed. Every step tells you exactly what to do.

## Table of Contents

- [Before Your First Project (One-Time Setup)](#before-your-first-project-one-time-setup)
- [Creating a New Project (Do This For Every New App)](#creating-a-new-project-do-this-for-every-new-app)
- [Starting a Claude Code Session](#starting-a-claude-code-session)
- [The Manual Steps After Bootstrap](#the-manual-steps-after-bootstrap)
- [Day-to-Day Workflow Summary](#day-to-day-workflow-summary)
- [Troubleshooting](#troubleshooting)

---

## Before Your First Project (One-Time Setup)

You only do this section once, ever. Skip it entirely for your second project onward.

### Install the tools

1. Open the **Terminal** app (it's in Applications → Utilities, or search "Terminal" in Spotlight)

2. You'll see a window with a blinking cursor. This is where you type commands. After typing each command below, press **Return** (Enter) to run it. Wait for it to finish before typing the next one — you'll know it's done when you see your cursor blinking on a fresh line again.

3. Copy and paste each of these lines one at a time. Some will take a few minutes and show a lot of text scrolling by — that's normal:

```
brew install ruby
```

> **Why Ruby?** macOS ships with Ruby 2.6 which is too old for Fastlane's bundler. Homebrew Ruby (4.x) is required.

```
brew install xcodegen
```

```
brew install fastlane
```

```
brew install swiftlint
```

```
brew install lefthook
```

```
brew install gitleaks
```

```
brew install gh
```

4. If the very first command (`brew install xcodegen`) gives you an error like "command not found: brew", you need to install Homebrew first. Paste this and press Return:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then try the `brew install` commands again.

5. Authenticate the GitHub CLI. Paste this and follow the prompts it gives you:

```
gh auth login
```

It will ask you questions — choose "GitHub.com", "HTTPS", "Yes" to authenticate with browser, then it opens your browser to confirm.

### Install Claude Code MCP servers

These give Claude Code superpowers (building, GitHub access, Apple docs lookup). You install them once and they work for all projects.

Paste each of these one at a time in Terminal:

```
claude mcp add --transport stdio XcodeBuildMCP -- npx -y xcodebuildmcp@latest mcp
```

```
claude mcp add --transport stdio apple-docs -- npx -y @kimsungwhee/apple-docs-mcp@latest
```

```
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

```
claude mcp add --transport stdio xcode -- xcrun mcpbridge
```

For the GitHub MCP, you need a personal access token. Go to https://github.com/settings/tokens, click "Generate new token (classic)", check the `repo` and `workflow` boxes, click Generate, and copy the token. Then paste this command but replace `ghp_YOUR_TOKEN_HERE` with the token you just copied:

```
claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_YOUR_TOKEN_HERE -- npx -y @modelcontextprotocol/server-github
```

### Install Claude Code plugins

Start Claude Code by typing `claude` in Terminal and pressing Return. Then inside the Claude Code session, type each of these:

```
/plugin install code-review@claude-plugins-official
```

```
/plugin install frontend-design@claude-plugins-official
```

```
/plugin install telegram@claude-plugins-official
```

Type `/exit` to leave Claude Code when done.

---

## Creating a New Project (Do This For Every New App)

This is the part you'll repeat for every new app.

### Step 1: Create the bootstrap script file

You only create this file once. After that, you just edit 4 lines each time.

1. Open **TextEdit** (search for it in Spotlight)

2. Go to TextEdit menu → **Format** → **Make Plain Text** (important — rich text will break the script)

3. Open the playbook file (`_playbook/ios-project-playbook.md`), find the section called "0.2 One-Command Project Bootstrap", and copy the entire code block — everything between the opening ` ```bash ` and the closing ` ``` `. It starts with `#!/bin/bash` and ends with the `echo` lines.

4. Paste it into your TextEdit document.

5. Save it as `bootstrap.sh` inside your `_playbook` folder:
   - File → Save
   - Navigate to: `iCloud Drive > Code > _playbook`
   - Filename: `bootstrap.sh`
   - If TextEdit tries to add `.txt`, uncheck "If no extension is provided, use .txt"

### Step 2: Edit the 4 variables for your new app

Before each new project, open `bootstrap.sh` in TextEdit and change only these 4 lines near the top:

```
APP_NAME="MyApp"
BUNDLE_ID="com.example.myapp"
REPO_NAME="myapp"
MINIMUM_IOS="26.0"
```

Save the file after editing. That's it — don't change anything else in the script.

### Step 3: Run the script

1. Open Terminal

2. Navigate to your Code folder by pasting this and pressing Return:

```
cd ~/Code
```

> **Note:** Replace `~/Code` with wherever you keep your projects. The playbook
> examples use `~/Code` throughout — substitute your actual path if different.

3. Run the bootstrap script:

```
bash '_playbook/bootstrap.sh'
```

4. Watch the output. It will print a bunch of lines as it creates files. At the end you should see:

```
✅ MyApp bootstrapped successfully!
```

Followed by a list of manual steps. If you see any red error text, something went wrong — the error message usually tells you what.

**What just happened:** The script created a `MyApp/` folder inside your Code folder with an entire Xcode project, Fastlane config, GitHub Actions workflows, SwiftLint config, pre-commit hooks, legal doc templates, and more. It also created a GitHub repo and pushed everything to it.

### Step 4: Set up the pre-commit hooks

If you saw `⚠️  Lefthook not installed` during bootstrap, install it now:

```
brew install lefthook
```

Then run (from your project folder):

```
cd '~/Code/MyApp'
```

```
lefthook install
```

If bootstrap completed without that warning, this step is already done — skip ahead.

### Step 5: Customize CLAUDE.md (first Claude Code session)

The bootstrap script already created `CLAUDE.md` in your project with your app name,
bundle ID, and URL scheme filled in. The remaining project-specific sections (core problem,
core loop, tech stack, UI direction, scope list) are best filled in during your first
Claude Code session.

1. If you have a product spec from a previous Claude chat, download it (e.g., `MyApp_Spec.md`)
   and drop it into your project folder: `iCloud Drive > Code > myapp`

2. Start Claude Code (see "Starting a Claude Code Session" below)

3. Tell it something like:
   - "Fill in CLAUDE.md using the spec in MyApp_Spec.md" (if you have a spec), or
   - "Let's fill in the CLAUDE.md — here's what the app does: [describe your app]"

4. Claude Code will fill in the sections, commit, and push — no manual git commands needed.

---

## Starting a Claude Code Session

Every time you sit down to work on your project:

1. Open Terminal

2. Navigate to your project:

```
cd '~/Code/MyApp'
```

3. Start Claude Code:

```
claude
```

That's it. Claude Code will read your `CLAUDE.md` and spec automatically.

**If you want Telegram remote access** (so you can check on Claude from your phone):

```
claude --channels plugin:telegram@claude-plugins-official
```

### Things you can type inside Claude Code

These are slash commands — type them at the Claude Code prompt, not in Terminal:

```
/feature PointCloudRenderer       — scaffold a new feature (View + ViewModel + Tests)
/test LASImporter                 — generate tests for a module
/review                           — review your current changes for issues
/code-review                      — multi-pass code review (official plugin)
/mcp                              — check MCP server connections
/plugin                           — check plugin status
/exit                             — leave Claude Code
```

### To end a session

Type `/exit` or press `Ctrl+C` twice. Claude Code will have already committed
your changes if you asked it to.

---

## The Manual Steps After Bootstrap

The bootstrap script prints a list of things it cannot do for you. Here's
what each one means and how to do it:

**1. Register bundle ID in Apple Developer Portal**
- Go to https://developer.apple.com/account/resources/identifiers
- Click the **+** button
- Select "App IDs" → "App"
- Enter description (e.g., "MyApp") and bundle ID (`com.example.myapp`)
- Check any capabilities you need (e.g., HealthKit, App Groups)
- Click Continue → Register

**2. Create app record in App Store Connect**
- Go to https://appstoreconnect.apple.com
- Click My Apps → **+** → New App
- Select iOS, enter name, select your bundle ID, set SKU (e.g., "myapp")
- Click Create

**3. Create provisioning profile**
- Go to https://developer.apple.com/account/resources/profiles
- Click **+** → Distribution → App Store Connect
- Select your bundle ID → select your distribution certificate
- Name it exactly: `"MyApp App Store"`
- Download the `.mobileprovision` file
- Base64 encode it (paste this in Terminal):

```
base64 -i ~/Downloads/MyApp_App_Store.mobileprovision | pbcopy
```

(This copies the encoded text to your clipboard)

**4. Add GitHub Secrets**
- Go to your repo on github.com → Settings → Secrets and variables → Actions
- Click "New repository secret" for each:

| Name | Value |
|---|---|
| `PROVISIONING_PROFILE` | Paste the base64 text from step 3 (it's on your clipboard) |
| `PROVISIONING_PROFILE_NAME` | `MyApp App Store` (exact name from step 3) |
| `APP_STORE_CONNECT_API_KEY` | Contents of your `.p8` file (same across all apps) |
| `ASC_KEY_ID` | Your API Key ID (same across all apps) |
| `ASC_ISSUER_ID` | Your Issuer ID (same across all apps) |
| `CERTIFICATE_P12` | Your base64-encoded certificate (same across all apps) |
| `CERTIFICATE_PASSWORD` | Your certificate password (same across all apps) |

The last four are the same across all your apps — they come from your Apple Developer
account, not from a previous repo. Keep these values in a password manager so you can
paste them into each new project. If this is your first project, see Phase 1 in
`ios-project-playbook.md` for how to generate each value.

**5. Create `.env.fastlane` for local deploys**
- In the project root, create a file called `.env.fastlane` (it's already gitignored):

```
ASC_KEY_ID=YOUR_ASC_KEY_ID
ASC_ISSUER_ID=YOUR_ASC_ISSUER_ID
ASC_KEY_FILEPATH=~/Documents/Xcode/AuthKey_YOUR_ASC_KEY_ID.p8
```

- The `.p8` key lives at `~/Documents/Xcode/AuthKey_YOUR_ASC_KEY_ID.p8` (shared across all apps)
- The Key ID and Issuer ID are the same across all your apps — only `ASC_KEY_FILEPATH` could change if you move the key
- This enables the `/deploy` slash command to upload to TestFlight from your machine
- To test manually: `export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && set -a && source .env.fastlane && set +a && bundle exec fastlane beta`

**6. Enable GitHub Pages**
- Go to your repo on github.com → Settings → Pages
- Source: Deploy from a branch
- Branch: `main`, folder: `/docs`
- Click Save

---

## Day-to-Day Workflow Summary

Here's what a typical evening coding session looks like:

1. **Open Terminal**
2. **Navigate:** `cd '~/Code/MyApp'`
3. **Start Claude Code:** `claude`
4. **Tell it what to work on:** "Let's build the LAS file importer today"
5. **Claude Code works** — it reads your CLAUDE.md, checks the spec, writes code, builds with XcodeBuildMCP, fixes errors, commits to a feature branch
6. **When done:** Claude Code updates CLAUDE.md's "Current State" section and writes a detailed session diary entry to `WORKLOG.md`, then commits and pushes
7. **If there are manual tasks:** Claude Code writes them to `MANUAL-TASKS.md`
8. **When ready for TestFlight:** run `/deploy` — builds, signs, and uploads from your machine. No GitHub Actions credits needed

That's the whole workflow. Everything else (linting, secret scanning, conventional
commits, dependency updates) happens automatically in the background.

---

## Troubleshooting

Common issues you might hit during setup:

| Problem | Fix |
|---|---|
| `brew: command not found` | Install Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`. Follow the post-install instructions to add Homebrew to your PATH. |
| `xcodegen: command not found` after install | Close and reopen Terminal, or run `eval "$(/opt/homebrew/bin/brew shellenv)"` |
| `gh auth login` fails | Make sure you have a GitHub account. If using 2FA, select "Login with a web browser" when prompted. |
| Bootstrap script permission denied | Run `chmod +x _playbook/bootstrap.sh` then try again |
| `xcrun: error: unable to find utility` | Install Xcode command line tools: `xcode-select --install` |
| Ruby/bundler errors during Fastlane | macOS system Ruby is too old. Install Homebrew Ruby: `brew install ruby`, then prepend to PATH: `export PATH="/opt/homebrew/opt/ruby/bin:$PATH"` |
| Certificate import fails (`.p12`) | Ensure the password matches. Try importing via Keychain Access app (File → Import Items) instead of command line. |
| `gitleaks: command not found` in commit hook | The hook uses full paths, so run `brew install gitleaks`. If still failing, check `/opt/homebrew/bin/gitleaks` exists. |
| Build fails after Xcode update | Run `xcodebuild -runFirstLaunch` and check Xcode → Settings → Components for required iOS platform downloads. |
