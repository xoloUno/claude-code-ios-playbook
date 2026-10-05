# Playbook & Dev-Environment Refactor — Canonical Plan

> **Purpose:** the single durable reference for this multi-session initiative. If context
> is lost, start here. Last updated **2026-10-03**.
> **Status:** direction FINALIZED. **Stage 0 migration COMPLETE & verified (2026-05-30)** —
> all 7 repos now live in `~/dev`, fsck-clean, and Flara compiles from the new location.
> `~/dev` is canonical; the iCloud rollback copies were **deleted 2026-09-27**, closing Stage 0.
> **Stage 1a carve COMPLETE (2026-05-31)** — rules (`0113986`) + iOS commands (`e3ce3cc`)
> carved into `core/` + `packs/`; bootstrap output verified byte-identical both times.
> **Stage 1a iOS bridge done (2026-05-31)** — `compose-claude.sh` + genericized deploy markers
> (`40c2ed5`); all 3 iOS apps bridged to the pinned `_playbook` submodule and **merged 2026-05-31**
> (Flara #55, broadsheet #1, teewye #1). **Commands architecture DESIGNED (2026-06-01)** — universal
> skeleton + per-kind `command-profile.md` + `project.yml` facts (see `COMMANDS-ARCHITECTURE.md`);
> added `_playbook/CLAUDE.md` operating guide. **Phase A COMPLETE (2026-06-01, branch
> `feat/universal-status-wrapup`)** — universal `/status`+`/wrapup` skeletons +
> `packs/{ios,python}/command-profile.md` + the playbook's `command-profile.local.md`; compose
> copies the profile; `PLAYBOOK_PATH`→`$PLAYBOOK_HOME`; conform Checks A/C/F pack-aware; templates
> deleted; both gates green. **Phase B COMPLETE & MERGED (2026-06-01)** — `bridge-symlink.sh` +
> the three non-iOS repos bridged via live symlinks, one PR each (`_playbook` #15→main `fabb66c`;
> devpulse #1→main `b59e4bd`; shotsmith #2→main `9be2c57`; c3d #19→`docs/architecture-phase2`
> `b5bccc5`); conform Check B made bridge-aware in the same `_playbook` PR. **Rules pass COMPLETE (2026-06-01,
> branch `refactor/git-workflow-truly-core`)** — `core/rules/git-workflow.md` is now truly core
> (iOS-isms — `[skip ci]`, "Current State", `WORKLOG`, release-notes, Swift globs, `dev`-only,
> `ui` — deferred to `/wrapup` + the iOS `command-profile`, mostly deletion); both gates green,
> the `packs/<pack>/rules` bridge loop stays latent (no non-iOS pack ships rules yet).
> **Phase C `/test` DONE & MERGED (2026-06-01, PR #20)** — split the overloaded
> verb: `/test` is now a universal *run-the-declared-suite* skeleton (`project.yml` `test_command`
> → kind default `pytest -q` / `xcodebuild test` → clean no-op), and the old iOS test-*generation*
> command moved to `packs/ios/commands/gen-tests.md`. Bridge now links six universal verbs (`test`
> added); `/conform` Check B/C updated in lockstep; CHANGELOG entry added. **shotsmith re-bridged +
> `test_command` fixed (shotsmith#3) — its `/test` is live; devpulse/c3d can re-bridge when next
> touched (both no-op).** Remaining Phase C verbs (`/context-health`, `/preflight`) stay
> deferred-on-contact — neither has forcing contact yet. **Stage 1b STARTED (2026-06-01, branch
> `feat/stage1b-marketplace-plugin`)** — Phase 1: the playbook now ships as a Claude marketplace
> plugin (`.claude-plugin/{marketplace,plugin}.json` + a single namespaced `/playbook:upgrade`
> recompose verb under `plugin/commands/`); `compose-claude.sh` verified self-locating and
> byte-identical when run from a plugin cache; local-directory dry-run confirmed the plugin exposes
> exactly one component (~22 always-on tok) with no stray repo leakage. **Phase 1 landed on `main`
> (`ef631ed`) and shipped as `playbook@playbook` v1.0.1, tag `playbook--v1.0.1`.** **Phase 2 — Flara
> canary DONE (2026-06-02):** cold-start install + idempotent no-diff `/playbook:upgrade` verified on
> Flara `main` (#56, `aebc758`); legacy submodule + `.playbook-version` removed. **WWDC26 wave
> folded in (2026-06-10):** Xcode 27 beta (27A5194q) verified hands-on — new
> `packs/ios/rules/wwdc26-ios27.md`, two-surface localization split in `metadata-translation.md`
> (+ `TRANSLATION.md` glossary contract), Decision A amended (Apple first-party skills > Hudson
> for the overlap; Hudson → SwiftData/Concurrency only), Xcode 27 facts in §7. **Next: Phase 3 —
> broadsheet + teewye** (same recipe, one PR each).
> **Modernization review + `AGENTS.md` canary (2026-10-01 → 03):** a Claude Code / Codex review of
> what changed since June converged (decisions in §2). Approved and merged: project instructions
> move to `AGENTS.md` with a generated core block, and `CLAUDE.md` becomes a relative symlink to it
> (playbook #32 → `0b51f99`; teewye canary #2 → `53c4826`). **Next: the bounded rollout in §4
> Stage 1c. It's proposed and awaiting approval.**

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
| **A** | Overlap with Paul Hudson's MIT Swift skills (code-style, testing, review/test cmds) | **Keep voice + vendor-reference Hudson.** Strip generic mechanics; keep scar-tissue. **Amended 2026-06-10:** Xcode 27 ships seven first-party skills (verified, exported from 27A5194q) — prefer Apple for the overlapping ground (SwiftUI best practices + SDK-27 changes, XCTest→Swift Testing migration, security audit, UIKit modernization, device interaction); Hudson narrows to the confirmed gaps (**SwiftData, Concurrency** — no Apple skill covers them). Voice + scar-tissue still never outsourced. |
| **B** | Kickstart's role | **Free/optional only.** Its paid tier duplicates first-party tooling (shotsmith); only free Overdrive (≈ open-source ControlRoom) is additive. |
| **Dist** | How elaborate to go | **Staged hybrid.** Symlink/submodule is an *interim bridge*; iOS apps graduate to a Claude marketplace. "MCP/skills only when earned." |
| **Codex** | Sequencing | **Phase 2.** Design the shared source Codex-aware from day one; build/​debug the Codex adapter + MCP + bake-off harness later, after the Claude path works end-to-end. |
| **Pinning** | Version primitive | **Semver `version` + git release tag** for your own marketplace (controlled rollout). **SHA-pin** only for the vendored Hudson fork and for freezing a release-critical consumer. |
| **Instr** (2026-10-01; symlink 2026-10-02) | Where project instructions live | **`AGENTS.md`**, holding project-owned text plus a generated "Shared workflow" block between `<!-- playbook:core:begin -->` / `<!-- playbook:core:end -->` markers. For opted-in projects the block replaces the six `core/rules/` copies. **`CLAUDE.md` is a relative symlink to `AGENTS.md`.** An `@AGENTS.md` import was rejected because it failed in fresh, unapproved headless test launches from a subdirectory. Compose accepts only that exact alias. |
| **Fail** (2026-10-01) | Compose failure contract | Validate the layout and every required source (each pack's `required.txt`, the universal commands, core) **before writing anything**. A failure after writing begins is reported as possibly partial. No automatic restore and no undo promise. |

## 3. Target architecture — "skill-first, plugin-wrapped, MCP-backed"

```
ONE playbook repo (source of truth)
  core/ + packs/{ios,python,cli}
  authored as portable Agent Skills (SKILL.md) + a generated always-on stub
        │
        ├── Claude adapter  (.claude-plugin/plugin.json) ──► your Claude marketplace
        ├── Codex adapter   (agents/openai.yaml)         ──► Phase 2
        └── stub  ──► AGENTS.md (generated core block + project text); CLAUDE.md = symlink to it

local stdio MCP  (Phase 2; highest maintenance + security surface, not "free")
  dynamic verbs only: bootstrap, capture_lesson, status/health, suggest_upgrade,
  get_project_profile, list_applicable_rules   — expose as MCP TOOLS, never prompts

PlaybookLauncher repo  = iOS factory (iOS pack + bootstrap + lifecycle + Keychain)
```

### Cross-cutting hardening rules (invariants — do not violate)
- **Correctness-critical rules live FLAT in the stub** (`CLAUDE.md`/`AGENTS.md`), never behind
  skill progressive disclosure — disclosure does **not** transfer across agents (Claude and
  Codex independently decide when to load `references/`, so "same file" ≠ "same tokens").
- **One instruction file.** `AGENTS.md` is the source and `CLAUDE.md` is a relative symlink to
  it (Decision **Instr**), so the two can't drift.
- **Every consumed dependency is vendored + pinned, and designed so its disappearance is a
  no-op** (exit test: Hudson vanishes → run the fork; Kickstart vanishes → lose a free
  convenience).
- **Dynamic verbs are MCP tools, not prompts** (Codex doesn't surface MCP prompts). *Proposed
  amendment (review item R5, pending Erik): verbs default to a skill plus a deterministic script,
  and a verb becomes an MCP tool only after a demonstrated limitation.*
- **Don't claim "one skill, identical on both agents"** — claim "shared source + per-agent
  adapters, parity verified by a written bake-off harness."

## 4. Sequence (status tracker)

- [x] **Stage 0 — Hygiene & safe migration** — COMPLETE (iCloud copies deleted 2026-09-27)
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
  - [x] **Memory-migration gap (found 2026-06-03; closed 2026-09-27):** Claude Code keys per-project
        memory by absolute path under `~/.claude/projects/<path-key>/memory/`, *outside* the repos, so
        the `rsync -a` repo copy never carried it. **Resolved by copying forward (option b):** the four
        app keys (Flara, c3d, teewye, broadsheet) now hold every file from their old iCloud keys
        (verified 2026-09-27, nothing only-in-old), and the `Code` root key's plan memory lives in the
        `~/dev` key. The `_playbook` key was missed. On 2026-09-27 its one still-valid rule (public
        repo, so no PII) was restored into the `~/dev` key and its stale TerraView bootstrap note was
        dropped. The dead iCloud-path keys stay in `~/.claude/projects/`, unaffected by the iCloud
        delete; prune them whenever.
  - [x] **iCloud copies deleted (2026-09-27, Erik).** `~/dev` had been the daily-use location since
        2026-05-30. Post-delete sweep: all 8 repos `git fsck`-clean, `$PLAYBOOK_HOME` →
        `~/dev/_playbook`, no symlinks or git worktrees pointing into iCloud. Harmless leftovers:
        stale allowlist entries in the gitignored `settings.local.json` of `_playbook` and Flara, and
        old project keys in `~/.claude.json`. `command-reference.md` was moved to `~/dev` first.
        **`Code/_ref/` and `Code/archive/` were never part of the migration and went with the folder**;
        if either is needed, check iCloud Drive → Recently Deleted (kept ~30 days).
  - [x] push `_playbook` `main` to origin — `origin/main` has tracked `main` via PRs since Stage 1a
- [ ] **Stage 1a — Bridge (drift stops fast):** carve `core/` + `packs/`; symlink into Python
  utils, submodule into iOS apps; **de-bootstrap** each (delete old copied commands/rules so
  they don't shadow the shared source)
  - [x] carve rules → `core/rules` + `packs/ios/rules` (commit `0113986`)
  - [x] carve iOS commands → `packs/ios/commands` (commit `e3ce3cc`); bootstrap output verified byte-identical
  - [x] extract `compose-claude.sh` (shared by bootstrap **and** the bridge, so they can't drift)
  - [x] genericize deploy commands with per-project markers `__PROVISIONING_PROFILES__` /
        `__METADATA_LOCALES__` (+ existing `__PRIMARY_SIM__`) — found Flara had woven its ASC
        profiles + es-ES/es-MX locales into `release.md`; markers let each app fill specifics at
        compose time so the bridge refreshes generic source without clobbering project config
  - [x] submodule bridge for the 3 iOS apps — `_playbook` pinned to playbook `main` (`442f469`),
        `.claude/` recomposed via `compose-claude.sh`, inbox repointed to `~/dev/_playbook`,
        `_playbook` SwiftLint-excluded. Flara's profiles/12 locales in `.env.project`, its app-only
        `media-handling.md` preserved. Bridged via `chore/playbook-bridge` per app and **merged
        2026-05-31** (Flara #55→main, broadsheet #1→dev, teewye #1→main).
  - [x] `build-deploy.md` standardized on Flara's **Shotsmith** pipeline (Erik's call). 10-agent-style
        audit (`wf_dbe31b39`) verified per-app Fastfiles: Flara+teewye on shotsmith, broadsheet on
        frames-cli with no widget/LA/CC surfaces. Rule now names Shotsmith the standard composer, keeps
        only common lanes literal, defers surface-specific lane names to each Fastfile (`fastlane --list`)
        — drift-free across all 3, byte-identical again.
  - [ ] migrate broadsheet's Fastfile frames-cli → Shotsmith (spun off as a broadsheet-session task;
        needs simulators + re-capture). Then all 3 Fastfiles match the shared standard.
  - [x] reviewed + merged the three `chore/playbook-bridge` branches to app mains (2026-05-31)
  - [x] **universal `/status`+`/wrapup` + non-iOS symlink bridge** — designed in
        `COMMANDS-ARCHITECTURE.md` (3-tier: skeleton + per-kind `command-profile.md` + `project.yml`
        facts, runtime-bound). **Phase A DONE (2026-06-01, branch `feat/universal-status-wrapup`)** —
        rewrote `{status,wrapup}.md` to the universal skeleton + load-first hook; authored
        `packs/{ios,python}/command-profile.md` + the playbook's `command-profile.local.md`; compose
        copies the profile; `PLAYBOOK_PATH`→`$PLAYBOOK_HOME` across inbox/conform/upgrade/playbook-inbox;
        conform Checks A/C/F pack-aware; `git rm`'d `templates/commands/{status,wrapup}.md`; CHANGELOG entry
        + 3 supersession banners. Both gates green: byte-identical iOS compose (only
        status/wrapup/conform/inbox/upgrade differ + new `command-profile.md`; composed inbox path
        stays absolute) and lossy-extraction coverage for all four variants. **Phase B DONE &
        MERGED (2026-06-01)** = built `bridge-symlink.sh` (surgical/idempotent live-symlink bridge)
        + bridged all three non-iOS repos, one PR each (devpulse #1, shotsmith #2 +`project.yml`,
        c3d #19 +`command-profile.local.md`/no pack; `_playbook` script #15); bespoke commands
        `git rm`'d → mode-120000 symlinks; conform Check B made bridge-aware; all merged
- [~] **Stage 1b — Graduate (controlled rollout):** iOS apps → your Claude marketplace,
  `autoUpdate:true` + semver `version`/tag; retire `.playbook-version`/`/upgrade` as primary,
  keep a `/conform` drift-check verb
  - [x] **Phase 1 — marketplace scaffolding (2026-06-01, branch `feat/stage1b-marketplace-plugin`)** —
        design is **compose-as-plugin**: the marketplace plugin bundles `compose-claude.sh` + `core/`
        + `packs/` (plugin source `"./"` = repo root) and exposes ONE namespaced verb
        `/playbook:upgrade` that recomposes a consumer's `.claude/` from `${CLAUDE_PLUGIN_ROOT}`. This
        sidesteps the two plugin limits (commands are force-namespaced → universal verbs stay
        un-namespaced, written by compose; plugins can't ship always-on `.claude/rules/` → rules stay
        real cached files via compose). On-demand refresh, `autoUpdate:true` for source only;
        `/conform` stays the drift detector; marker substitution kept (no `project.yml` migration this
        round). `claude plugin validate` passes; compose byte-identical from a plugin-cache path;
        release target is the first contract tag `playbook--v1.0.0` (created on `main` after merge).
  - [x] **Phase 2 — Flara canary (DONE 2026-06-02)** — Flara #56 merged at `aebc758` commits the
        marketplace `.claude/settings.json` (github `playbook` marketplace + `playbook@playbook` +
        `autoUpdate:true`). Cold-start from a wiped global plugin cache verified: trust accepted
        (`hasTrustDialogAccepted`), `playbook` marketplace registered, `playbook@playbook` **v1.0.1**
        installed project-scoped to Flara from `ef631ed` / tag `playbook--v1.0.1`. `/playbook:upgrade`
        recompose from the installed plugin was **idempotent — byte-identical, 0-byte diff, clean
        tree**. Legacy gone: no `_playbook` submodule, no `.gitmodules`, no `.playbook-version` (the
        stale `442f469` pin is retired).
  - [ ] **Phase 3 — broadsheet-app + teewye-app (NEXT)** — same recipe as Flara, one PR each.
  - [ ] **Phase 4 — retire legacy** (composed `/upgrade`; teach `bootstrap.sh` to birth new apps on
        the marketplace; wire version-bump + tag into the playbook's `/wrapup` contract).
- [~] **Stage 1c — Instruction layout (`AGENTS.md`). Canary DONE; rollout PROPOSED (2026-10)**
  - [x] Modernization review converged (Claude Code + Codex, 2026-10-01).
  - [x] **Generator and validation, playbook #32 → `0b51f99`:**
        - `core/agents-core.md`
        - `compose-agents-md.py`
        - the compose source preflight, with each pack's `required.txt`
        - commands that read and write the instructions file
        - 30 tests, with legacy output pinned to a reviewed fixture
  - [x] **teewye canary, #2 → `53c4826`.** Passed:
        - loading from the repo root and a subdirectory: desktop Claude Code 2.1.286 checked
          against transcript content; Xcode-hosted 2.1.154 checked by hook; Codex CLI 0.136.0
          run with `--ignore-user-config`, because the configured model was unsupported
        - `/conform`: no false missing-core or template findings; six existing advisory section
          gaps
        - `/wrapup` changing only the project-owned section
        - a recompose reproducible from the pinned commit
        - session-start instructions 87.8 → 78.8 KB

        **Caveats:**
        1. Test-command resolution was only partial: an honest skip (no test target), and the
           `[APP_NAME]` scheme placeholder needed manual substitution.
        2. `/wrapup`'s commit attempt was blocked by the test copy's guard, so the commit, hook
           and push steps weren't exercised.
        3. Xcode-hosted Claude was checked by hook only.

        Not validated: the user's normal Codex configuration, and authenticated Xcode-hosted
        workflows.
  - [ ] **Rollout. PROPOSED, awaiting Erik's approval. One project per PR, and Erik approves
        each.** Scope: core instruction delivery only. Rule scoping (review item R2) stays
        separately gated.
        - **Step 0, prerequisites (playbook PRs):**
          - (a) Make `bridge-symlink.sh` opt-in aware. For a non-iOS repo whose `AGENTS.md`
            carries the markers, it skips the core-rule symlinks and renders the block with
            `compose-agents-md.py write`. Today it would re-create core-rule symlinks, which
            current Claude Code doesn't load without approval anyway.
          - (b) Fix the never-substituted `[APP_NAME]` scheme placeholder (inbox, 2026-10-03).
          - (c) Bump the plugin version and tag before Flara's turn. Flara consumes
            `playbook@playbook`, still at 1.0.1.
        - **Step 1, broadsheet-app** (iOS, submodule, 11 KB `CLAUDE.md`): the teewye recipe, a
          refresh commit then a layout commit. Stage 1b Phase 3 (moving to the plugin) stays a
          separate, later PR.
        - **Step 2, devpulse** (smallest non-iOS), after Step 0(a). It's the first run of the
          non-iOS path, and it also fixes the undelivered symlinked core rules there.
        - **Step 3, shotsmith, then c3d-bridge-modeler** (non-iOS), as separate project PRs.
          Use shotsmith to verify the real-suite `/test` path; verify the emitted iOS command
          resolves its scheme without manual substitution in broadsheet or a disposable iOS
          fixture. Creating app test targets is not required for this migration. c3d's
          `CLAUDE.md` is 21.9 KB, so check the total against Codex's 32 KiB default.
        - **Step 4, Flara last.** It needs three things first:
          - the oversized-instructions fix: its `CLAUDE.md` is 140 KB, so session history moves
            to a tracked archive through a reviewed extraction, approved separately
          - Step 0(c)
          - a gap between releases
        - **Step 5, new projects:** `bootstrap.sh` and `CLAUDE-TEMPLATE.md` emit the `AGENTS.md`
          layout.
        - **Per-project acceptance:**
          - **Preservation.** Compare project text and history against the approved edits.
            Preserve substitutions, local profiles and customized rules. Remove only verified
            unmodified core copies or known core links.
          - **Layout.** Verify:
            - one matching block
            - the exact alias
            - no duplicate core loading
            - the expected pack guidance
          - **Refresh.** Confirm a rerender is idempotent, and that the core and alias are
            unchanged during a disposable `/wrapup`. For pinned or installed playbooks, confirm a
            recompose reproduces the tree. For live bridges, record the source revision and
            demonstrate the block-refresh path.
          - **Loading.** Test from the root and a subdirectory on the hosts each project actually
            uses. Keep unverified hosts as recorded caveats.
          - **`/conform`.** No false missing-core or template findings.
          - **Budget.** Instructions within budget.
          - **Record.** The source commit or installed version, the host versions, and the
            authentication and Codex configuration used.

          A real commit or hook test belongs only in an explicitly authorized disposable copy,
          with push disabled.
  - [ ] **Other review items. Proposed, not approved:**
        - R2: rule scoping, `globs:` → `paths:` or skills, since `globs:` is ignored (§7)
        - R3: the remaining behavior fixes in pack rules
        - R4: a Codex workflow-parity experiment
        - R5: the MCP invariant amendment (§3)
        - R6 (Xcode `mcp-server`), R7 (`.xcproj`) and R9 (tool evaluations): deferred until
          needed
        - R8: measure Frames 1.5.0 in isolation before any upgrade; it changes default bezels
        - R10: a baseline toolchain step

        Evidence lives in the review log, which is kept locally and not in this repo. Status
        changes land here once approved.
- [ ] **Stage 2 — Apple skills first, Hudson for gaps (re-scoped 2026-06-10, Decision A
  amendment):** adopt Apple's exported Xcode 27 skills for the overlapping ground
  (refresh = re-run the export per Xcode release; link into `~/.claude/skills` for Claude);
  vendor Hudson SHA-pinned only for SwiftData + Concurrency; thin overlapping Swift rules
  against the *Apple* skills, not Hudson's
- [ ] **Stage 3 — Codex + MCP + bake-offs:** `AGENTS.md` from the same stub; verbs as MCP
  tools; written bake-off harness before any comparison. *(Update 2026-10-03: instruction
  delivery to Codex is now Stage 1c, `AGENTS.md` plus the `CLAUDE.md` symlink. Stage 3 keeps
  Codex workflow parity, MCP and bake-offs.)* **Note (2026-06-10):** Xcode 27's
  agents are a *third* `AGENTS.md`/`CLAUDE.md` consumer (verified — its localization agents
  auto-read both), strengthening the one-source stub invariant; and Apple's own localization
  flow (coordinator + sub-agents over MCP *tools*, never prompts) is first-party precedent
  for exactly the MCP-tool verb design locked here
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
> **Resolution → `COMMANDS-ARCHITECTURE.md`:** one universal skeleton + per-kind `command-profile.md`
> + `project.yml` facts, bound at runtime; the four drifted variants collapse to one source.

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

**Instruction loading (tested 2026-10-01 → 03, each fact with its evidence):**

- **Claude Code reads only `paths:` in rule frontmatter.** `globs:` is ignored, so those rules
  load at session start. Documented, and tested on 2.1.141 and 2.1.284 with an
  `InstructionsLoaded` hook.
- **Rules symlinked from outside the project didn't load on 2.1.284** in a headless test (they
  did on 2.1.141). The docs treat such links like external imports, which need approval. This
  affects `bridge-symlink.sh` repos.
- **`CLAUDE.md` = `@AGENTS.md` loaded `AGENTS.md` from the repo root, but not in fresh,
  unapproved headless launches from a subdirectory.** The relative symlink loaded from both:
  desktop 2.1.286 checked against transcript content, Xcode-hosted 2.1.154 checked by hook.
  Whether an interactive approval restores nested imports wasn't tested.
- **Xcode-hosted Claude is 2.1.154,** which predates Claude Code's direct `AGENTS.md` support
  (2.1.277).
- **Codex has no `@include` syntax,** reads `AGENTS.md` from the git root down to the working
  directory, and caps combined project instructions at 32 KiB by default (`project_doc_max_bytes`).
- **Staleness note:** several June facts below are out of date. For example, claude-code#52218
  closed 2026-05-31, plugin installs no longer need `/reload-plugins`, and Xcode 27 GM adds a
  headless `xcrun mcp-server`. A refresh is pending the baseline step (review item R10).

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

**Xcode 27 / WWDC26 facts (verified hands-on on beta 27A5194q, 2026-06-10; re-verify at GM):**

- **Skills export syntax is `xcrun mcpbridge run-agent skills export --output-dir <dir>
  --replace-existing`** — `xcrun agent` is an alias of `mcpbridge`; blog posts citing
  `xcrun agent skills export <dir>` are paraphrasing. Requires Xcode running. Seven skills:
  swiftui-specialist, swiftui-whats-new-27, test-modernizer, device-interaction,
  audit-xcode-security-settings, uikit-app-modernization, c-bounds-safety.
- **Claude Code does NOT read `~/.agents/skills`** (verified empirically — skills there
  don't appear in sessions); only `~/.claude/skills` / project `.claude/skills`. Codex/
  Gemini/Cursor read `~/.agents/skills`.
- **`mcpbridge` tools are session-scoped to a workspace tab** — headless `tools/list`
  never returns (initialize succeeds, server `xcode-tools`). Enumerate from an
  Xcode-attached session. New 27 tool families: `DeviceInteraction*`/`DeviceEventSynthesize`
  and `LocalizationPlanner`/`StringCatalog{Read,Context,Edit}`.
- **Xcode 27 launches agents itself**: `run-agent claude` execs an Apple-signed Claude
  binary under `~/Library/Developer/Xcode/CodingAssistant/Agents/XcodeVersions/<build>/`
  with its own `CLAUDE_CONFIG_DIR` and a one-server (`xcode-tools`) `--mcp-config`.
- **Localization agents**: coordinator + sub-agents (batches ≤15 strings, ≤3 concurrent)
  over String Catalog MCP tools; output marked "Machine Translated"; they auto-read
  `AGENTS.md`/`CLAUDE.md`/referenced files (e.g. `TRANSLATION.md`). 16 bundled locale
  style guides — **no Spanish, no Portuguese** (the project glossary carries es/pt).
- **`@State` is a macro in SDK 27** (source-breaking; reorder-the-init is the wrong fix) —
  Apple's `swiftui-whats-new-27` skill is the authority.
- Announced, not independently verified: Xcode 27 Apple-silicon-only; MCP + Agent Client
  Protocol plugin extensibility; Swift 6.4; Foundation Models additions (image input,
  server models, third-party model protocol); new Core AI framework. `DeviceHub.app`
  exists inside the Xcode-beta bundle (verified present, not exercised).

## 8. Build-vs-buy policy

- **CONSUME (first-party, version = the Xcode release):** Apple's seven Xcode 27 agent
  skills — refresh by re-running the skills export after each Xcode update; link into
  `~/.claude/skills` for Claude Code (it ignores `~/.agents/skills`). Exit test: Apple
  skills vanish → playbook rules still stand alone. *(Added 2026-06-10, Decision A
  amendment.)*
- **CONSUME (vendored + SHA-pinned):** Hudson's MIT Swift code-quality skills — narrowed
  2026-06-10 to **SwiftData + Concurrency only** (Apple's skills now own SwiftUI +
  Testing). Fork, record the SHA, refresh on your cadence with a diff
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
- [x] iCloud copies deleted 2026-09-27 (see §4 Stage 0).
- [x] `_playbook` `main` is on origin (see §4 Stage 0).
- [ ] shotsmith still has 1 uncommitted file (present in both copies) — commit/stash when convenient.
- [x] **Stage 1a carve** — rules (`0113986`) + iOS commands (`e3ce3cc`) carved into `core/`+`packs/`; bootstrap output verified byte-identical.
- [x] **Stage 1a commands — Phase A DONE (2026-06-01)** — universal `/status`+`/wrapup`
  skeletons + load-first hook; `packs/{ios,python}/command-profile.md` + the playbook's own
  `command-profile.local.md`; compose copies the profile; `PLAYBOOK_PATH`→`$PLAYBOOK_HOME`;
  conform Checks A/C/F pack-aware; templates `git rm`'d. Branch `feat/universal-status-wrapup`,
  both gates green.
- [x] **Stage 1a Phase B DONE & MERGED (2026-06-01)** — `bridge-symlink.sh` + the three non-iOS
  repos symlink-bridged, one PR each (`_playbook` #15→main `fabb66c`; devpulse #1→main `b59e4bd`;
  shotsmith #2→main `9be2c57` +`project.yml`; c3d #19→`docs/architecture-phase2` `b5bccc5`
  +`command-profile.local.md`, no pack). Bespoke `/status`+`/wrapup` (+ shotsmith `/context-health`)
  `git rm`'d → mode-120000 symlinks; conform Check B made bridge-aware (non-iOS expects exactly the
  bridged five) in the same `_playbook` PR. iOS apps already submoduled + merged.
- [x] **Rules pass DONE (2026-06-01, branch `refactor/git-workflow-truly-core`)** — handoff:
  `RULES-PASS-HANDOFF.md`. Made `core/rules/git-workflow.md` **truly core**: `globs` → `**/*`,
  `main` + `feature/*`/`fix/*` with `dev` noted optional, dropped/genericized the `ui` type and the
  App-Store tag example, removed the dead `YourOrg/[REPO_NAME]` placeholder, and **deferred the
  session-end record steps** (`[skip ci]`, CLAUDE "Current State", `WORKLOG`, `release-notes-draft`)
  to `/wrapup` + the project's `command-profile`. The iOS `command-profile.md` `## /wrapup` already
  owned `[skip ci]` + release notes, so this was **mostly deletion — no new `packs/ios/` rule**.
  Gates green: iOS compose still carries every git behavior (relocated to the profile); the live
  symlink in devpulse / shotsmith / c3d-bridge-modeler now serves the cleaned rule. CHANGELOG entry
  added; `COMMANDS-ARCHITECTURE.md` "Related cleanup" marked done. The second follow-up — a
  **`packs/<pack>/rules` loop** in `bridge-symlink.sh` — stays **latent**: no non-iOS pack has a
  `rules/` dir yet (packs/python + packs/cli are command-profile-only), so there was nothing to
  link; the script already carries the comment marking where to add it.
- [~] **Phase C — generalize on contact** (handoff: `PHASE-C-HANDOFF.md`):
  - [x] **`/test` DONE & MERGED (2026-06-01, PR #20)** — universal
    run-the-declared-suite skeleton (`.claude/commands/test.md`) + `## /test` in
    `packs/{ios,python}/command-profile.md`; iOS test-*generation* renamed to
    `packs/ios/commands/gen-tests.md` (content unchanged). Coupled surfaces updated in the same PR:
    `bridge-symlink.sh` `COMMANDS` (+`test`, six verbs), `/conform` Check B (+`test`, both sides)
    and Check C (`test`→`gen-tests`), `packs/README.md`, CHANGELOG. Decision (run vs generate split)
    recorded in `COMMANDS-ARCHITECTURE.md`. Gates: byte-identical iOS compose except the intended
    `test.md`/`gen-tests.md`/`command-profile.md`.
    - **Re-bridge to gain the `test` symlink is per-repo and one-time** (a *new* universal command
      needs it; existing ones propagate through their symlinks). Sequence is ordered — the `_playbook`
      PR must reach `main` first, else the committed symlink dangles. **shotsmith DONE & MERGED
      (shotsmith#3):** re-bridged + corrected its `project.yml` `test_command` to `python3 -m pytest -q`
      (bare `pytest` wasn't on PATH); `/test` is live and verified green (101 passed). **devpulse + c3d:
      not yet re-bridged — they can re-bridge when next touched** (both no-op cleanly: devpulse has no
      tests, c3d declares no runner), so neither has `/test` until then.
  - [ ] **`/context-health`** — already universal+bridged; convert to skeleton+profile only when a
    kind-specific signal is wanted. No forcing contact yet.
  - [ ] **`/preflight`** — iOS-pack, deploy-coupled; leave iOS-pack unless a real non-iOS need
    appears (don't bridge for symmetry). No forcing contact yet.
- [x] **`/conform` Check G — silent-untrack detection DONE (2026-06-01, branch
  `feat/conform-untracked-rules-check`)** — adopted the `inbox.md` "curate residual" lesson:
  `/conform` now lists each on-disk `.claude/rules/*.md` via `git ls-files --error-unmatch` and
  uses `git check-ignore -v` to separate the silent gitignored case (Check A passes + `git status`
  clean, yet the rule is absent from version control and dies on a fresh clone) from a merely
  untracked-new file, reporting the offending `.gitignore` path:line:pattern. **Advisory — never
  rewrites the project-owned `.gitignore`.** This is the *detection* half; the `.gitignore`
  inline-comment / anchored-scratchpad *write* fix landed earlier (PR #18). Downstream-visible →
  CHANGELOG entry; byte-identical iOS compose except `conform.md`. Inbox entry retired.
- [ ] **Recommended near-term order:**
  0. **Stage 1c rollout (proposed, see §4).** broadsheet and teewye migrate to `AGENTS.md`
     before their Stage 1b Phase 3 plugin move, as separate PRs.
  1. **Stage 1b — IN PROGRESS.** Phase 1 (marketplace plugin scaffolding + `/playbook:upgrade`)
     landed on `main` (`ef631ed`, tag `playbook--v1.0.1`). Phase 2 (**Flara canary**) is **DONE
     (2026-06-02)** — cold-start install + idempotent no-diff `/playbook:upgrade` verified on Flara
     `main` (#56, `aebc758`). **Next:** Phase 3 — broadsheet + teewye (same recipe, one PR each),
     then Phase 4 (retire composed `/upgrade`; teach `bootstrap.sh`; wire tag into `/wrapup`).
     `/upgrade` is retired-as-primary in favor of `/playbook:upgrade`; `/conform` stays the
     drift-check verb.
  2. **Stage 2 (re-scoped 2026-06-10):** adopt Apple's exported Xcode 27 skills for the
     overlapping ground; vendor Hudson SHA-pinned for SwiftData + Concurrency only; thin
     overlapping Swift/iOS guidance only after the command/rule surface has settled.
  3. **Stage 3:** Codex + MCP + bake-off harness when cross-agent tooling is the next priority.
  4. **Stage 4:** spin out PlaybookLauncher + Keychain migration as its own mini-project, not
     cleanup drift work.

## 10. References

- **Full review analysis:** workflow run `wf_e73fd29f-ed9` (10 agents; inventory + fact-check +
  4-lens critique + partition).
- **Commands architecture:** `COMMANDS-ARCHITECTURE.md` — universal + extensible commands design
  (supersedes the design portion of `~/.claude/plans/hazy-dreaming-ocean.md`; keeps its gotchas).
- **Private recall:** `~/.claude/.../memory/playbook-dev-env-refactor.md` (auto-loads each session).
- Paul Hudson skills: [twostraws/swift-agent-skills](https://github.com/twostraws/swift-agent-skills),
  [twostraws/swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill) (MIT).
- Kickstart: [kickstart.tools/mcp](https://www.kickstart.tools/mcp).
- Agent Skills standard: agentskills.io. `npx skills` = github.com/vercel-labs/skills.
- Codex docs: developers.openai.com/codex/{plugins/build, mcp, skills, guides/agents-md}.
- Claude Code docs: code.claude.com/docs/en/{plugins, skills, mcp, hooks, discover-plugins}.
