# Claude Code Plugins & MCP Servers for iOS Development

Setup guide for extending Claude Code with iOS-specific tooling. These are
**development-time tools** that make Claude Code sessions more productive.
They do NOT replace the production CI/CD pipeline (Fastlane + XcodeGen +
GitHub Actions) — that infrastructure stays exactly as-is.

**What these add:** Claude Code can build your project, read errors, manage
simulators, check GitHub Actions logs, and review code — all without you
copy-pasting terminal output or switching windows.

## Table of Contents

- [How It Works (Quick Primer)](#how-it-works-quick-primer)
- [Tier 1 — Install These First](#tier-1--install-these-first)
- [Tier 2 — Add When Comfortable](#tier-2--add-when-comfortable)
- [Tier 3 — Situationally Useful](#tier-3--situationally-useful)
- [Keeping Everything Up to Date](#keeping-everything-up-to-date)
- [Quarterly Plugin Maintenance](#quarterly-plugin-maintenance-jan--apr--jul--oct)
- [What NOT to Install](#what-not-to-install-and-why)
- [Verifying Your Setup](#verifying-your-setup)
- [Adding to Your CLAUDE.md Template](#adding-to-your-claudemd-template)

---

## How It Works (Quick Primer)

- **Plugins** = bundles of skills, commands, and agents. Installed via `/plugin`
  inside Claude Code. Stored in `~/.claude/`.
- **MCP servers** = connections to external tools (GitHub, Xcode, etc.). Added
  via `claude mcp add` in your terminal. Claude Code auto-discovers them.
- **Skills** = markdown instruction files that teach Claude Code when and how
  to use specific tools. Often bundled inside plugins.

Plugins and MCP servers are toggle-able — enable/disable per session without
breaking anything. Unused servers don't consume context tokens until activated.

---

## Tier 1 — Install These First

### 1. GitHub MCP Server (Official, by Anthropic)

Gives Claude Code direct access to your GitHub repos, issues, PRs, Actions
logs, and CI/CD status. Instead of you checking why a TestFlight deploy
failed, Claude Code reads the Actions log itself.

**Install:**

```bash
# You need a GitHub Personal Access Token (classic or fine-grained)
# with repo, workflow, and read:org scopes.
# If you already authenticated gh CLI, you can reuse that token.

claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_YOUR_TOKEN_HERE -- npx -y @modelcontextprotocol/server-github
```

**What it enables Claude Code to do:**
- Check GitHub Actions build status and read failure logs
- Create issues and PRs
- Search across your repos
- Read file contents from any branch

**Verify it works:** Start a Claude Code session and ask:
"Check the latest GitHub Actions run for this repo — did it pass?"

---

### 2. XcodeBuildMCP

The most impactful MCP server for iOS development. Claude Code can trigger
Xcode builds, read structured error output, run tests, and manage simulators
— all without you touching the terminal.

**Install:**

```bash
claude mcp add --transport stdio XcodeBuildMCP -- npx -y xcodebuildmcp@latest
```

**Optional environment variables for better performance:**

```bash
claude mcp add --transport stdio XcodeBuildMCP \
  --env INCREMENTAL_BUILDS_ENABLED=true \
  --env XCODEBUILDMCP_DYNAMIC_TOOLS=true \
  -- npx -y xcodebuildmcp@latest
```

**What it enables Claude Code to do:**
- Build your project and read errors as structured JSON (not raw logs)
- Run unit tests and UI tests
- List and boot simulators
- Install and launch on simulator
- All in a tight fix-build-fix loop without you intervening

**Verify it works:** Open Claude Code in a project directory and ask:
"Build this project for iPhone 17 Pro simulator and show me any errors."

**Important:** This is for LOCAL sessions only. Cloud sessions (claude.ai
connected to GitHub) still cannot run xcodebuild — the CI pipeline handles
that via GitHub Actions, which remains unchanged.

---

### 3. Apple Platform Build Tools Plugin

A Claude Code plugin (not MCP server) with reference documentation for the
entire xcrun ecosystem and a subagent that handles builds cleanly.

**Install (inside Claude Code):**

```
/plugin install apple-platform-build-tools@apple-platform-build-tools-claude-code-plugin
```

Or add to your project's `.claude/settings.json` so it's always available:

```json
{
  "enabledPlugins": {
    "apple-platform-build-tools@apple-platform-build-tools-claude-code-plugin": true
  },
  "extraKnownMarketplaces": {
    "apple-platform-build-tools-claude-code-plugin": {
      "source": {
        "source": "github",
        "repo": "kylehughes/apple-platform-build-tools-claude-code-plugin"
      }
    }
  }
}
```

**What it adds:**
- Agent Skill with reference docs for xcodebuild, simctl, devicectl,
  code signing, profiling, distribution, and binary tools
- Subagent that runs builds and returns structured results without
  polluting the main context window

**Complements XcodeBuildMCP:** XcodeBuildMCP is the raw build tool.
This plugin adds the knowledge layer — Claude Code knows *how* to use
xcodebuild flags correctly, not just that it can call it.

---

### 4. Apple Developer Documentation MCP Server

**This directly replaces the manual "look up APIs before writing code" rule
in CLAUDE.md.** Instead of Claude Code needing to remember to search the web,
it gets a dedicated tool that queries Apple's official documentation JSON API
directly — framework references, symbol lookups, WWDC videos, code examples,
and beta/deprecated status tracking across all Apple platforms.

There are two options. Pick one:

**Option A: `apple-docs-mcp` by kimsungwhee** (recommended — simpler, npm-based)

```bash
claude mcp add --transport stdio apple-docs -- npx -y @kimsungwhee/apple-docs-mcp@latest
```

What it exposes:
- Smart search across all Apple frameworks (SwiftUI, UIKit, Metal, HealthKit, etc.)
- Full documentation access via Apple's JSON API
- Framework index — browse hierarchical API structures
- Technology catalog for all platforms (iOS, macOS, watchOS, tvOS, visionOS)
- Beta API and deprecation tracking (critical for iOS 26 work)

**Option B: `apple-doc-mcp` by MightyDillah** (more features, more setup)

```bash
# Requires cloning the repo and building locally
git clone https://github.com/MightyDillah/apple-doc-mcp.git
cd apple-doc-mcp && npm install && npm run build
claude mcp add --transport stdio apple-docs -- node /absolute/path/to/apple-doc-mcp/dist/index.js
```

Extra features: persistent symbol indexing, wildcard search (`Grid*`, `*Item`),
camelCase tokenization, framework-specific caching. More powerful but heavier.

**Verify it works:** In Claude Code, ask:
"Look up the current API for ActivityKit Live Activities on iOS 26."

**How this changes your CLAUDE.md rule:** Replace the manual "STOP and look up
the current API first" instruction with:

```markdown
### Framework Verification Rule
Before writing code using any Apple framework introduced at or after WWDC25,
Claude Code MUST use the apple-docs MCP tool to verify the current API. This
is automatic — do not rely on training knowledge for new APIs.
```

---

### 5. Xcode Native MCP Bridge (requires Xcode 26.3+)

Apple shipped a built-in MCP server in Xcode 26.3. It exposes 20 native tools
via `xcrun mcpbridge`, including a **DocumentationSearch** tool that does
semantic search across Apple developer docs and WWDC transcripts. This is
Apple's own documentation search, running locally.

**Install:**

```bash
claude mcp add --transport stdio xcode -- xcrun mcpbridge
```

**Prerequisites:** Xcode 26.3+ must be running with a project open. The bridge
connects to Xcode's process via XPC.

**What it exposes (20 tools across 5 categories):**

| Category | Tools |
|---|---|
| File operations | XcodeRead, XcodeWrite, XcodeUpdate, XcodeGlob, XcodeGrep, XcodeLS, XcodeMakeDir, XcodeRM, XcodeMV |
| Build & test | BuildProject, GetBuildLog, RunAllTests, RunSomeTests, GetTestList |
| Code analysis | XcodeListNavigatorIssues, XcodeRefreshCodeIssuesInFile |
| Execution & preview | ExecuteSnippet, **RenderPreview** |
| Discovery | **DocumentationSearch**, XcodeListWindows |

The standout tools for you:
- **DocumentationSearch** — semantic search across Apple docs including WWDC
  transcripts. This is the most authoritative source possible — it's Apple's
  own search, not a third-party scraper.
- **RenderPreview** — Claude Code can render SwiftUI previews and *see* the
  result visually. For your app's UI work this means Claude can verify its
  layout changes actually look right.
- **BuildProject / GetBuildLog** — overlaps with XcodeBuildMCP but runs
  through Xcode's own build system rather than raw `xcodebuild`.

**How this relates to XcodeBuildMCP:** They complement each other.
XcodeBuildMCP works without Xcode running (59 tools, standalone via CLI).
Apple's bridge requires Xcode running but gives you previews, documentation
search, and deeper IDE integration (20 tools). Use both — Claude Code will
pick the right one based on the task.

**Note:** Apple's MCP bridge is newer and less documented. XcodeBuildMCP is
the more battle-tested option. Start with XcodeBuildMCP as your primary
build tool and add the Xcode bridge for documentation search and previews.

---

## Tier 2 — Add When Comfortable

### 6. Official Code Review Plugin

Free from Anthropic's built-in marketplace. Runs a structured multi-pass
code review: security, test coverage, error handling, simplification.

**Install (inside Claude Code):**

```
/plugin
```

Then go to the **Discover** tab → find `code-review` → install.

Or from the command line:

```
/plugin install code-review@claude-plugins-official
```

**Use it:** Run `/code-review` after finishing a feature to get a second
pair of eyes before merging.

---

### 7. Frontend Design Plugin (Official Anthropic)

Activates specialized UI/UX knowledge when building interfaces — accessibility,
responsive patterns, design system thinking.

**Install (inside Claude Code):**

```
/plugin install frontend-design@claude-plugins-official
```

**When to use:** Before building any new UI view, especially for apps where
design quality matters (all of them, but particularly consumer-facing ones
like consumer-facing apps).

---

### 8. xclaude-plugin (Modular iOS Toolkit)

8 workflow-specific MCP servers with 24 tools. Enable only what you need
to keep context lean.

**Install:**

```bash
# Add the marketplace first
claude plugin marketplace add conorluddy/xclaude-plugin

# Then install the plugin
/plugin install xclaude@xclaude-plugin
```

**The modules (enable selectively):**

| Module | Tokens | What it does |
|---|---|---|
| xc-build | ~600 | Build + structured error extraction |
| xc-launch | ~400 | Simulator install + launch |
| xc-interact | ~900 | UI interaction via accessibility tree |
| xc-ai-assist | ~1400 | Code edit → build → screenshot loop |
| xc-setup | ~500 | Environment discovery |
| xc-testing | ~800 | Test execution + results |
| xc-meta | ~300 | Maintenance tasks |
| xc-all | ~3500 | Everything enabled |

**Start with:** `xc-build` + `xc-launch` for a ~1000-token composable
build-and-run loop. Add `xc-interact` when you need UI verification.

---

## Tier 3 — Situationally Useful

### 9. Telegram Plugin (Official Anthropic)

Connects a Telegram bot to your Claude Code session, giving you mobile
access. DM the bot from your phone and messages go straight to the active
session — Claude's responses come back in the chat. Useful for:
- Checking on long-running builds when you're away from your Mac
- Sending quick instructions to a session from your phone
- Getting notified when Claude Code finishes a task

**Install:**

```bash
# Step 1: Create a Telegram bot via @BotFather in Telegram
#   - Send /newbot, follow prompts, get your bot token

# Step 2: Add the plugin
/plugin install telegram@claude-plugins-official
```

**Start a session with Telegram connected:**

```bash
claude --channels plugin:telegram@claude-plugins-official
```

On first use, DM your bot — it replies with a 6-character pairing code.
Enter the code and you're connected. After pairing, switch to allowlist
mode so strangers can't message your bot.

**Practical use case for you:** Start a Claude Code session on your Mac,
kick off a build or a multi-file refactor, then walk away. Check progress
from your phone via Telegram. Send "what's the status?" or "push to dev
when you're done" from anywhere.

---

### 10. Context7 MCP (Third-Party Library Docs)

Fetches version-specific documentation for **non-Apple** third-party libraries
directly into Claude Code sessions. The Apple Docs MCP (Tier 1) handles Apple
frameworks — Context7 handles everything else: RevenueCat, Lottie, Firebase,
or any SPM dependency where Claude's training data may be stale.

**Install:**

```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

**When it's useful:**
- Working with RevenueCat SDK (API changes between versions)
- Integrating any new SPM dependency you haven't used before
- When Claude Code generates code with methods that don't exist
  (hallucinated APIs) — Context7 grounds it in real docs

**Two tools it exposes:**
- `resolve-library-id` — looks up a library
- `query-docs` — fetches specific documentation sections

Less critical for pure Apple frameworks (your CLAUDE.md API verification
rule handles that), but valuable for third-party libraries.

---

### 11. Axiom iOS Plugin (Community)

13 production-ready skills for Swift/Xcode development from a community
marketplace. Covers common iOS patterns, architecture decisions, and
Swift idioms.

**Install:**

```bash
# Add the marketplace
claude plugin marketplace add jeremylongshore/claude-code-plugins-plus-skills

# Install the plugin
/plugin install axiom@claude-code-plugins-plus-skills
```

**What it adds:** Skills for Swift patterns, Xcode project management,
testing strategies, and iOS-specific best practices. Think of it as a
senior iOS dev's cheat sheet baked into Claude Code's awareness.

**Worth trying after** you're comfortable with the Tier 1 and 2 tools
and want Claude Code to have deeper iOS-specific pattern knowledge.

---

### 12. claude-superpowers (Swift-Focused Community Collection)

A curated collection of Claude Code plugins and skills specifically for
Swift development, code migration, and AI-assisted workflows.

**Install:**

```bash
claude plugin marketplace add ivan-magda/claude-code-marketplace
```

Browse available plugins after adding, then install what looks relevant.

---

## Keeping Everything Up to Date

### The Problem

Plugins and MCP servers are a fast-moving ecosystem. What's best today may
be deprecated, forked, or superseded in 3–6 months. There's no single
"update all" button that also checks for deprecation or better alternatives.

### What's Automated

**Plugin auto-updates:** Official Anthropic marketplace plugins have
auto-update enabled by default. When you start Claude Code, it checks for
new versions and updates automatically. You can verify this:

```
/plugin
```

Look at the Updates tab. If a plugin has a pending update, apply it there.

**MCP server updates:** MCP servers installed via `npx -y` always pull
the latest version on each launch (that's what the `-y` flag does — it
skips the cache and fetches fresh). So XcodeBuildMCP, GitHub MCP, and
Context7 are effectively self-updating every time you start Claude Code.

**Force update a specific plugin:**

```
/plugin update <plugin-name>
```

**Force update all plugins:**

```
/plugin update --all
```

### What's NOT Automated (and How to Handle It)

There's no built-in way to check whether a plugin has been deprecated or
whether something better has come along. Here's a low-friction routine:

**Quarterly check (put a recurring calendar reminder):**

1. **Check official marketplace:** Run `/plugin` → Discover tab. Scan for
   new official Anthropic plugins. New iOS-relevant ones will stand out.

2. **Check your installed plugins for health:**
   ```
   /plugin
   ```
   Look at the Errors tab. If a plugin is throwing errors consistently,
   it may be unmaintained. Check its GitHub repo — look at last commit
   date and open issues.

3. **Check MCP server repos:**
   - XcodeBuildMCP: https://github.com/getsentry/XcodeBuildMCP (npm: xcodebuildmcp)
   - GitHub MCP: https://github.com/modelcontextprotocol/servers
   - Context7: https://github.com/upstash/context7

   If a repo is archived or hasn't been touched in 6+ months, start
   looking for alternatives.

4. **Quick web search:** Ask Claude (in this chat, not Claude Code) to
   search for "best Claude Code MCP servers iOS development [current year]"
   — the landscape changes fast enough that a fresh search every few months
   is genuinely useful.

5. **Check the awesome lists:**
   - https://github.com/jmanhype/awesome-claude-code
   - https://github.com/ccplugins/awesome-claude-code-plugins
   - https://claudemarketplaces.com

### One-Liner for a Quick Health Check

Run this inside Claude Code to get a snapshot of everything installed:

```
/mcp
```

Then:

```
/plugin
```

If any MCP server shows "disconnected" or any plugin shows errors,
investigate that specific one. Everything else is likely fine.

### If You Want to Automate the Reminder

Add this to your iOS Project Playbook or personal task list:

```
## Quarterly Plugin Maintenance (Jan / Apr / Jul / Oct)

- [ ] Run `/plugin` — check Updates and Errors tabs
- [ ] Run `/plugin update --all`
- [ ] Run `/mcp` — verify all servers connected
- [ ] Check official marketplace Discover tab for new iOS-relevant plugins
- [ ] Quick web search: "Claude Code iOS development plugins [year]"
- [ ] Check GitHub repos of installed MCP servers for activity
- [ ] Remove anything that's broken or superseded
```

---

## What NOT to Install (and Why)

| Tool | Why skip it |
|---|---|
| Database MCPs (PostgreSQL, Supabase, SQLite) | Your apps are local-first with no backend |
| Multi-agent swarm tools | Overkill for solo dev, 2–5 hrs/week |
| Figma MCP | Only useful if you design in Figma |
| Docker MCP | No containerized services in your stack |
| Slack/Discord/Notion MCPs | No team communication to integrate |

---

## Verifying Your Setup

After installing, run this in Claude Code to confirm everything is connected:

```
/mcp
```

This shows all active MCP servers and their status. You should see:
- `github` — connected
- `XcodeBuildMCP` — connected
- `apple-docs` — connected
- `xcode` — connected (only when Xcode is running)

Then run `/plugin` to see installed plugins and their status.

---

## Adding to Your CLAUDE.md Template

Add this section to your project CLAUDE.md files so Claude Code knows
about the available tools:

```markdown
## Available Plugins & MCP Servers

This project has the following Claude Code extensions available in local sessions:

- **XcodeBuildMCP** — use for building, testing, and simulator management.
  Prefer this over raw `xcodebuild` shell commands.
- **Xcode MCP Bridge** (`xcrun mcpbridge`) — use for documentation search,
  SwiftUI preview rendering, and real-time code diagnostics. Requires Xcode
  running with the project open.
- **Apple Docs MCP** — use for looking up Apple framework APIs before writing
  code. This replaces the manual "search developer.apple.com" rule. Claude
  Code should query this tool automatically when using any framework introduced
  at or after WWDC25.
- **GitHub MCP** — use for checking CI status, reading Actions logs,
  creating issues and PRs.
- **Apple Platform Build Tools** — reference docs for xcrun ecosystem.
  Consult the Agent Skill when composing complex xcodebuild commands.
- **Context7** — fetch current docs for third-party libraries (RevenueCat,
  etc.) when training data may be stale.

Cloud sessions do not have access to these tools. Use GitHub Actions for
build verification in cloud sessions (push to branch → Build Check workflow).

**Telegram channel:** Start with `claude --channels plugin:telegram@claude-plugins-official`
to enable mobile monitoring of long-running sessions via Telegram DM.
```

---

## Keeping Things Clean

- Run `/mcp` periodically to check server health
- Disable servers you're not actively using to save context tokens
- MCP servers auto-start when Claude Code launches — if you notice
  slowness, check which servers are running
- Plugin updates: `/plugin update <name>` or enable auto-update
- To remove an MCP server: `claude mcp remove <name>`
- To disable a plugin: `/plugin disable <name>`
