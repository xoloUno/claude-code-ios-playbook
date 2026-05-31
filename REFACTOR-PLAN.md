# Playbook & Dev-Environment Refactor — Canonical Plan

> **Purpose:** the single durable reference for this multi-session initiative. If context
> is lost, start here. Last updated **2026-05-30**.
> **Status:** direction FINALIZED. **Stage 0 migration COMPLETE & verified (2026-05-30)** —
> all 7 repos now live in `~/dev`, fsck-clean, and Flara compiles from the new location.
> `~/dev` is canonical; iCloud copies retained as rollback pending deletion approval.
> **Stage 1a carve COMPLETE (2026-05-31)** — rules (`0113986`) + iOS commands (`e3ce3cc`)
> carved into `core/` + `packs/`; bootstrap output verified byte-identical both times.
> Next: the Stage 1a project-side **bridge** + **de-bootstrap** (first touches the app repos).

---

## 1. Objectives

1. **Migrate** active repos off iCloud (`~/Library/Mobile Documents/com~apple~CloudDocs/Code/`)
   to a local `~/dev/`. The real motive is stability — iCloud can evict `.build`/`.git`
   objects to `.icloud` stubs under disk pressure. Introduce `$PLAYBOOK_HOME` so paths stop
   being hardcoded.
2. **Make `_playbook` universal** — split the iOS-only playbook into `core/` + packs
   `{ios, python, cli}`. (The split already exists de facto: iOS apps carry a full
   bootstrap-emitted command set; Python projects carry few-to-none.)
3. **Distribute cross-agent (Claude Code + Codex)** so playbook updates propagate without
   the per-project `/upgrade` ritual (drift is the pain being solved).
4. **Spin out `PlaybookLauncher`** (a macOS SwiftUI GUI over `bootstrap.sh`, currently inside
   `_playbook`) into its own repo = the iOS app factory. Move ASC/Team secrets to Keychain.

## 2. Locked decisions (2026-05-30)

| # | Decision | Choice |
|---|---|---|
| **A** | Overlap with Paul Hudson's MIT Swift skills (code-style, testing, review/test cmds) | **Keep voice + vendor-reference Hudson.** Strip generic mechanics; keep scar-tissue. |
| **B** | Kickstart's role | **Free/optional only.** Its paid tier duplicates first-party tooling (shotsmith); only free Overdrive (≈ open-source ControlRoom) is additive. |
| **Dist** | How elaborate to go | **Staged hybrid.** Symlink/submodule is an *interim bridge*; iOS apps graduate to a Claude marketplace. "MCP/skills only when earned." |
| **Codex** | Sequencing | **Phase 2.** Design the shared source Codex-aware from day one; build/​debug the Codex adapter + MCP + bake-off harness later, after the Claude path works end-to-end. |
| **Pinning** | Version primitive | **Semver `version` + git release tag** for your own marketplace (controlled rollout). **SHA-pin** only for the vendored Hudson fork and for freezing a release-critical consumer. |

## 3. Target architecture — "skill-first, plugin-wrapped, MCP-backed"

```
ONE playbook repo (source of truth)
  core/ + packs/{ios,python,cli}
  authored as portable Agent Skills (SKILL.md) + a generated always-on stub
        │
        ├── Claude adapter  (.claude-plugin/plugin.json) ──► your Claude marketplace
        ├── Codex adapter   (agents/openai.yaml)         ──► Phase 2
        └── stub  ──► generated to BOTH CLAUDE.md and AGENTS.md from one source

local stdio MCP  (Phase 2; highest maintenance + security surface, not "free")
  dynamic verbs only: bootstrap, capture_lesson, status/health, suggest_upgrade,
  get_project_profile, list_applicable_rules   — expose as MCP TOOLS, never prompts

PlaybookLauncher repo  = iOS factory (iOS pack + bootstrap + lifecycle + Keychain)
```

### Cross-cutting hardening rules (invariants — do not violate)
- **Correctness-critical rules live FLAT in the stub** (`CLAUDE.md`/`AGENTS.md`), never behind
  skill progressive disclosure — disclosure does **not** transfer across agents (Claude and
  Codex independently decide when to load `references/`, so "same file" ≠ "same tokens").
- **Generate `CLAUDE.md` and `AGENTS.md` from ONE source** so they can't drift.
- **Every consumed dependency is vendored + pinned, and designed so its disappearance is a
  no-op** (exit test: Hudson vanishes → run the fork; Kickstart vanishes → lose a free
  convenience).
- **Dynamic verbs are MCP tools, not prompts** (Codex doesn't surface MCP prompts).
- **Don't claim "one skill, identical on both agents"** — claim "shared source + per-agent
  adapters, parity verified by a written bake-off harness."

## 4. Sequence (status tracker)

- [x] **Stage 0 — Hygiene & safe migration** — done & verified; only the held iCloud-delete remains
  - [x] gitignore/​de-iCloud `.build`/build artifacts (removed `Flara/build`, 568 MB)
  - [x] `$PLAYBOOK_HOME` indirection: `~/.config/playbook/config` (source of truth) +
        `~/.zshenv` loader + `bootstrap.sh` honors it + `/upgrade` resolves via it.
        **Verified**; committed to `_playbook` `main` (local, not pushed).
  - [x] `$PLAYBOOK_HOME` resolution verified (fresh shell → `~/dev/_playbook`)
  - [x] `git fsck --full` clean on all 7 → migrated via **`rsync -a`** (chosen over clone to preserve
        gitignored secrets in one pass; iCloud copies untouched = rollback) → fsck-clean in `~/dev`
  - [x] real build in `~/dev` (Flara compiles; FlaraKit resolves to the new path); keepers verified
        (`.env.playbook` / `.env.project` / `.env.fastlane` / `WORKLOG` / `MANUAL-TASKS`)
  - [x] config repointed → `~/dev/_playbook`; `getting-started.md` paths fixed (downstream
        `playbook-inbox.md` left fallback-only → Stage 1; gitignored `settings.local.json` regenerable)
  - [ ] **HELD (irreversible, awaits Erik):** delete iCloud copies once `~/dev` is confirmed in daily use
  - [ ] (optional) push `_playbook` `main` to origin for off-machine backup
- [ ] **Stage 1a — Bridge (drift stops fast):** carve `core/` + `packs/`; symlink into Python
  utils, submodule into iOS apps; **de-bootstrap** each (delete old copied commands/rules so
  they don't shadow the shared source)
  - [x] carve rules → `core/rules` + `packs/ios/rules` (commit `0113986`)
  - [x] carve iOS commands → `packs/ios/commands` (commit `e3ce3cc`); bootstrap output verified byte-identical
  - [ ] project-side bridge (symlink Python utils, submodule iOS apps) + de-bootstrap each
- [ ] **Stage 1b — Graduate (controlled rollout):** iOS apps → your Claude marketplace,
  `autoUpdate:true` + semver `version`/tag; retire `.playbook-version`/`/upgrade` as primary,
  keep a `/conform` drift-check verb
- [ ] **Stage 2 — Vendor Hudson (SHA-pinned fork):** thin the ~4 overlapping Swift rules
- [ ] **Stage 3 — Codex + MCP + bake-offs:** `AGENTS.md` from the same stub; verbs as MCP
  tools; written bake-off harness before any comparison
- [ ] **Stage 4 — Spin out PlaybookLauncher:** iOS factory + Keychain (close BOTH secret
  stores: `.env.playbook` AND the `UserDefaults` copy)

## 5. Partition table (the build list)

All 16 rules + 18 command entries, verified against the real files. `^` = Decision-A-gated
(reference-Hudson alternative). `*` = Decision-B-gated (delegate-Kickstart alternative).
Defaults applied: keep first-party.

**iOS-pack skills (→ PlaybookLauncher):** build-deploy · legal-urls · status-bar-overrides ·
screenshot-pipeline`*` · asc-troubleshooting`*` · metadata-translation`*` · privacy-manifest`^` ·
wwdc25-ios26`^` · code-style`^` · testing`^` · + commands feature · test`^` · review`^` · deploy ·
release · preflight · capture-manual-surfaces

**Core skills (universal; each could collapse to a stub):** session-health · git-workflow
(mechanics only) · work-log · assertion-discipline (kernel; Apple examples move to iOS pack)

**Always-on stub (anti-fragmentation):** manual-tasks · playbook-inbox trigger

**MCP tools (dynamic verbs):** status (playbook + downstream variants) · wrapup (playbook +
downstream variants) · context-health · conform · inbox (= capture_lesson) · curate ·
upgrade (= suggest_upgrade)

**Retire:** none. `upgrade`/`conform` survive *because* verification proved no ecosystem
auto-updates silently across projects, so a staleness-check verb still earns its place.

> Subtlety: `/status` and `/wrapup` each exist in two forms — a playbook-repo variant and a
> downstream-iOS template that `bootstrap.sh` layers on top. c3d-bridge (non-iOS) runs renamed
> copies of the iOS templates, which is why those downstream verbs are project-agnostic.

## 6. Safe migration method (Stage 0 → clone)

**Ordering matters** (one variable at a time): `$PLAYBOOK_HOME` indirection FIRST while still
on iCloud (because `/upgrade` historically string-scrapes the hardcoded path), verify, then
move.

**Method (executed 2026-05-30):** **`rsync -a`** (excluding build/venv dirs) rather than clone —
preserves gitignored secrets/worklogs in one pass; iCloud copies left untouched as rollback;
`git fsck` after confirmed integrity on all 7. (Clone would have dropped the gitignored keepers.)

**Gotcha — clone drops what isn't committed:** `git clone` copies committed history only. It
will NOT bring over uncommitted changes or **gitignored** files — which for these repos
includes `.env.playbook`, `.env.fastlane`, `WORKLOG.md`, `MANUAL-TASKS.md`. Either `rsync -a`
(excluding `build/`/`.build`) and `fsck` after, or clone and then **explicitly copy the
gitignored keepers**. Do not assume your `.env` secrets came along.

**Pre-flight audit (run 2026-05-30):** all 7 repos fsck-clean; zero `.icloud` stubs anywhere;
every repo has an `origin` remote with 0 unpushed commits (full off-machine backup); hardcoded
path in only 4 tracked files (1 line each); only outstanding dirty item is **shotsmith** (1
uncommitted file — owner to handle). Nothing is broken today → migration is prudent, not an
emergency.

## 7. Verified facts (don't regress)

Corrections a 10-agent adversarial review made to the earlier draft. Full analysis archived at
the workflow output (run `wf_e73fd29f-ed9`).

- **Background updates are NOT a session-start hook.** Claude's native marketplace auto-update
  is the path, BUT third-party/own marketplaces have `autoUpdate` **OFF by default**, updates
  are **version-gated**, and it's **non-silent** (`/reload-plugins`); bug claude-code#52218
  leaves stale hook paths. Codex has **no auto-update daemon** (explicit
  `codex plugin marketplace upgrade` only). → `/upgrade`/`/conform` survive as a drift check;
  a hook is only a fallback for Codex / #52218.
- **The local MCP is free on dollars (no hosting) but is the highest-maintenance +
  highest-security component** (long-lived process with Keychain read = credential-exfil
  surface). Expose verbs as **tools**, not prompts.
- **`npx skills` is maintained by Vercel Labs (Guillermo Rauch), NOT Anthropic.** Pin the
  version or hand-copy SKILL.md + adapters; don't pipe `--yes` from untrusted repos. Codex/
  Gemini/Cursor share project `.agents/skills`; only Claude uses `.claude/skills`.
- **Codex IS first-class now:** plugins (`.codex-plugin/plugin.json`, marketplaces under
  `.agents/plugins/`), native skills (`SKILL.md` + optional `agents/openai.yaml`; skill ≠
  plugin), reads `AGENTS.md`/`AGENTS.override.md`. It probes `resources/list` at discovery but
  doesn't surface MCP prompts.
- **Kickstart pricing:** weekly is **$2.99**, not $4.99 (yearly $69.99 correct). Treat its
  marketing copy as claim-not-proof. macOS 26.2 + Apple-Silicon floor would block CI.
- **Secrets live in TWO places:** `.env.playbook` (cleartext) AND `LauncherViewModel` persists
  identity to `UserDefaults`. Keychain migration must close both; the `.p8` ASC key is the
  crown jewel — audit git history, rotate if ever committed.
- Anthropic doc URLs moved: `docs.anthropic.com/en/docs/claude-code/*` → `code.claude.com/docs/en/*`.

## 8. Build-vs-buy policy

- **CONSUME (vendored + SHA-pinned):** Hudson's MIT Swift code-quality skills (SwiftUI,
  SwiftData, Concurrency, Testing). Fork, record the SHA, refresh on your cadence with a diff
  review. Never auto-pull his HEAD.
- **REFERENCE (borrow, keep your voice):** all shipping-style/policy rules and scar-tissue.
- **NEVER outsource:** the factory (scaffold + xcodegen/fastlane + ASC/Keychain + lifecycle),
  the ASO/screenshot/metadata pipeline (shotsmith + frames-cli + screenshot-pipeline.md +
  metadata-translation.md), the lesson-capture loop, and any rule encoding a specific bug.
- **Kickstart:** free-tier/optional only. Free Overdrive ≈ open-source
  [twostraws/ControlRoom](https://github.com/twostraws/ControlRoom).

## 9. Open items / immediate next steps

- [x] Committed the two `_playbook` edits + this plan doc (branch `chore/playbook-home-indirection`,
  merged to `main` locally — not pushed).
- [x] Migration to `~/dev` done & verified (all 7 repos; Flara builds; secrets transferred).
- [ ] **HELD (irreversible):** delete the iCloud copies once `~/dev` is confirmed in daily use.
- [ ] (optional) `git push` `_playbook` `main` for off-machine backup.
- [ ] shotsmith still has 1 uncommitted file (present in both copies) — commit/stash when convenient.
- [x] **Stage 1a carve** — rules (`0113986`) + iOS commands (`e3ce3cc`) carved into `core/`+`packs/`; bootstrap output verified byte-identical.
- [ ] **Next: Stage 1a bridge** — symlink Python utils, submodule iOS apps, de-bootstrap projects (first changes that touch the app repos).

## 10. References

- **Full review analysis:** workflow run `wf_e73fd29f-ed9` (10 agents; inventory + fact-check +
  4-lens critique + partition).
- **Private recall:** `~/.claude/.../memory/playbook-dev-env-refactor.md` (auto-loads each session).
- Paul Hudson skills: [twostraws/swift-agent-skills](https://github.com/twostraws/swift-agent-skills),
  [twostraws/swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill) (MIT).
- Kickstart: [kickstart.tools/mcp](https://www.kickstart.tools/mcp).
- Agent Skills standard: agentskills.io. `npx skills` = github.com/vercel-labs/skills.
- Codex docs: developers.openai.com/codex/{plugins/build, mcp, skills, guides/agents-md}.
- Claude Code docs: code.claude.com/docs/en/{plugins, skills, mcp, hooks, discover-plugins}.
