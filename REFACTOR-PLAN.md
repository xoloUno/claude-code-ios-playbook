# Playbook & Dev-Environment Refactor — Canonical Plan

> **Purpose:** the single durable reference for this multi-session initiative. If context
> is lost, start here. Last updated **2026-10-22**.
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
> touched (both no-op).** *(Both were re-bridged in Stage 1c, 2026-10, and have `/test`.)*
> Remaining Phase C verbs (`/context-health`, `/preflight`) stay deferred-on-contact — neither
> has forcing contact yet. **Stage 1b STARTED (2026-06-01, branch
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
> for the overlap; Hudson → SwiftData/Concurrency only), Xcode 27 facts in §7. Phase 3 (broadsheet +
> teewye) is now on contact; see §9.
> **Modernization review + `AGENTS.md` canary (2026-10-01 → 03):** a Claude Code / Codex review of
> what changed since June converged (decisions in §2). Approved and merged: project instructions
> move to `AGENTS.md` with a generated core block, and `CLAUDE.md` becomes a relative symlink to it
> (playbook #32 → `0b51f99`; teewye canary #2 → `53c4826`).
> **Stage 1c rollout (2026-10-05 → 07):** Steps 0(a,b) and 1–3 are done, one PR per project with
> Erik's approval. broadsheet, devpulse, shotsmith and c3d-bridge-modeler now use `AGENTS.md`. The
> three non-iOS repos had been running without the shared rules on desktop Claude Code; the
> generated block fixed that. Step 4 (Flara) followed on 2026-10-07, and Step 5 (bootstrap) on
> 2026-10-08. **Stage 1c is done**, with the caveats recorded in §4.
> **Autonomy policy (2026-10-22):** the core gained an "Autonomy" section (#41 → `90fb81e`).
> Routine, reversible work runs without per-step approval; a fixed list still goes to the user.
> The sandbox, guard hook and installer from #43 and #44 were rolled back after the canary and
> removed in the lean cleanup (#45 → `e3c04f0`); autonomy now rests on auto mode, a few native
> rules and `PLAYBOOK_AUTONOMY=on`, and the owner switched it on the same day. All six opted-in
> projects were re-rendered the same day, so autonomy now applies in each; plugin installs are
> at `playbook--v1.2.3` (decision **Auto** in §2, steps in §9).
> **Xcode pin (2026-10-22, #53):** `bootstrap.sh` now gives new projects the lean Xcode pin
> piloted on Flara #65: one `.xcode-version` that CI reads at run time.
> **Maintenance mode (2026-10-22):** the modernization is done, and the playbook is no longer a
> project. Playbook work happens on contact: when a project hits a problem, or when a decision
> has a date. §9 lists what's left as on contact or parked.
> **Next:** project work (Flara, c3d-bridge-modeler, new projects).

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
   `_playbook`) into its own repo = the iOS app factory. (No Keychain move: since 2026-10-27
   the launcher holds no secrets, see §7.)

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
| **Auto** (2026-10-22) | Approval friction | **Autonomy policy** in the core block (#41 → `90fb81e`). Routine, reversible work runs without per-step approval: commits, feature-branch pushes, PRs, and merges that pass a checklist (tests and lint, CI where it exists, current `main`, and no open finding that meets the core "Code Review Rules" bar after one GitHub Codex bot review). A fixed list always goes to the user, parked in `MANUAL-TASKS.md`. Enforcement is Claude Code's auto mode plus the native rules in `settings/autonomy.json`: deny force pushes and explicit pushes to `main`, an auto-mode block on pushing `main` in any other form, and ask for fastlane lanes that reach App Store Connect; merges get a checklist because they can be reverted. No sandbox, hook, installer or word list: the 2026-10-22 canary showed the sandbox fenced the whole home folder and needed a growing exemption list. Claude keeps stock access to personal folders; any other local agent gets an OS-level read deny of them in its own config (`tools/codex-review.sh` shows the Codex profile). A local Codex review is an optional second opinion during development, never a merge item. `PLAYBOOK_AUTONOMY=on` switches it on; `autonomy: off` opts a project out. |

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
  - [ ] **Phase 3 — broadsheet-app + teewye-app (on contact, see §9)** — same recipe as Flara,
        one PR each.
  - [ ] **Phase 4 — retire legacy** (composed `/upgrade`; teach `bootstrap.sh` to birth new apps on
        the marketplace; wire version-bump + tag into the playbook's `/wrapup` contract).
- [x] **Stage 1c — Instruction layout (`AGENTS.md`). DONE (2026-10): the canary, Steps 0–4 (all
  six projects migrated) and Step 5 (new projects start in the layout). Caveats below.**
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
           `[APP_NAME]` scheme placeholder needed manual substitution. **Closed 2026-10-07:**
           #34 fills the scheme; broadsheet's composed `xcodebuild test` line passed with no
           manual substitution, and the real-suite `/test` passed on shotsmith (101) and c3d
           (201).
        2. `/wrapup`'s commit attempt was blocked by the test copy's guard, so the commit, hook
           and push steps weren't exercised. **Still open:** the broadsheet, devpulse,
           shotsmith and c3d `/wrapup` runs all had clean trees, so the commit step never
           fired. Flara had no `/wrapup` run at all, because the headless desktop binary's
           sign-in had expired.
        3. Xcode-hosted Claude was checked by hook only. **Still true** for every rollout
           project, Flara included.

        Not validated: the user's normal Codex configuration, and authenticated Xcode-hosted
        workflows. **Update 2026-10-07:** the normal Codex configuration (the CLI bundled in
        ChatGPT.app, 0.162.0-alpha.2, gpt-6.1-sol, high effort) loaded `AGENTS.md` from the root
        and a subdirectory on shotsmith, c3d and Flara. Authenticated Xcode-hosted workflows are
        still unvalidated.
  - [~] **Rollout. APPROVED, IN PROGRESS. One project per PR, and Erik approves each.** Scope:
        core instruction delivery only. Rule scoping (review item R2) stays separately gated.
        - **Step 0, prerequisites (playbook PRs):**
          - (a) **DONE, #35 → `d495f41`.** Make `bridge-symlink.sh` opt-in aware. For a
            non-iOS repo whose `AGENTS.md` carries the markers, it skips the core-rule symlinks
            and renders the block with `compose-agents-md.py write`. Re-running it is the
            block-refresh path.
          - (b) **DONE, #34 → `9d8140b`.** Fix the never-substituted `[APP_NAME]` scheme
            placeholder (inbox, 2026-10-03). Compose fills it from `XCODE_SCHEME`, else
            `project.yml`'s `name:`.
          - (c) **DONE 2026-10-07, #37 → `6f5770e`, tag `playbook--v1.1.0`.** `plugin.json`
            1.0.1 → 1.1.0, so the release includes #34 and #35. The CHANGELOG entry lists what
            a 1.0.1 consumer gets. Flara consumes `playbook@playbook`.
        - **Step 1, broadsheet-app. DONE, #4 → `f0d4931` (to `dev`).** iOS, submodule, 11 KB
          pre-migration `CLAUDE.md`: the teewye recipe, a refresh commit then a layout commit.
          Stage 1b Phase 3 (moving to the plugin) stays a separate, later PR.
        - **Step 2, devpulse. DONE, #2 → `de1d756`.** The first run of the non-iOS path.
          Before the switch, desktop Claude Code 2.1.286 loaded 0 of the 6 symlinked core rules;
          after it, the block is in context.
        - **Step 3, shotsmith, then c3d-bridge-modeler. DONE: shotsmith #6 → `a85eeb6`; c3d
          #22 → `11830be`.** shotsmith had no instruction file at all, so desktop sessions ran
          with no instructions; it now has a new `AGENTS.md`. c3d's `AGENTS.md` is 26.8 KB,
          under Codex's 32 KiB default, and it gained a `test_command` in `.claude/project.yml`.
        - **Open after Steps 1–3:** `/conform` Check D compares every project with the iOS
          `CLAUDE-TEMPLATE.md`, so devpulse, shotsmith and c3d get false template findings. That
          misses the `/conform` acceptance line below. Follow-up: a pack-aware Check D (inbox,
          2026-10-07).
        - **Step 4, Flara last. DONE 2026-10-07, flara-app #64 → `bac15ce`.**
          - Prerequisites, each in its own PR:
            - housekeeping: #61 → `b06b516`
            - the oversized-instructions fix: #63 → `c77ac24`, which took `CLAUDE.md` from
              141 KB to 22.8 KB, with detail moved to `spec/` and the archive to `history/`
            - Step 0(c)
            - a release gap: v2.1.2 was open and not yet submitted (it is live on the App
              Store as of 2026-10-22)
          - The local folder was renamed to `flara-app` to match the repo, which left the
            plugin's project-scope install record pointing at the old path. The plugin was
            reinstalled at 1.1.0.
          - #64 is a refresh commit from the installed plugin, then a layout commit (the
            broadsheet recipe). `AGENTS.md` is 26.7 KB.
          - Loading was checked from the root and `Flara/Views`:
            - desktop 2.1.293 and Xcode-hosted 2.1.154, by hook (both signed out headless, so
              content came from transcripts)
            - Codex 0.162, which answered a project question and a core question with no tool
              calls
          - `/conform` Checks A–G, reproduced by hand: no core, rule or command drift. Check F
            flags the Flara-only `media-handling.md`; Check D shows the same two advisory gaps
            as before.
        - **Step 5, new projects. DONE 2026-10-08, #39 → `211cf22`.**
          - Before compose runs, `bootstrap.sh` writes `AGENTS.md` from `CLAUDE-TEMPLATE.md`
            (empty core markers) and makes `CLAUDE.md` the relative symlink. Compose then renders
            the block and copies only the ios pack's rules. A missing template stops bootstrap.
          - New projects pin Xcode 27.1, which iPhone Duo needs, on GitHub's `xcode-27` runner,
            because `macos-26` has no Xcode 27. Build-check builds for a generic simulator.
          - Validation: two new tests (39 in all), and a full bootstrap dry run with `gh`
            stubbed. Codex: "ready to commit" on round 2.
          - **Follow-up, Xcode pin. Bootstrap DONE 2026-10-22, #53.** Flara #65 piloted a leaner
            pattern than writing the version into each workflow: one `.xcode-version` per app
            that CI reads at run time, checked against `project.yml`. It passed on its first CI
            run (inbox, 2026-10-21). `bootstrap.sh` now writes the file, and its three workflows
            read it; composed output is unchanged. teewye and broadsheet still pin Xcode 26.3 in
            their workflows; rolling the file out to them is next, one PR each.
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
- [ ] **Stage 4 — Spin out PlaybookLauncher:** iOS factory. The Keychain migration was
  dropped 2026-10-27: the launcher stopped collecting the ASC IDs, so neither of its stores
  holds a secret (see §7).

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

**Instruction loading (tested 2026-10-01 → 07, each fact with its evidence):**

- **Claude Code reads only `paths:` in rule frontmatter.** `globs:` is ignored, so those rules
  load at session start. Documented, and tested on 2.1.141 and 2.1.284 with an
  `InstructionsLoaded` hook.
- **Rules symlinked from outside the project didn't load on 2.1.284** in a headless test (they
  did on 2.1.141). The docs treat such links like external imports, which need approval. This
  affects `bridge-symlink.sh` repos. Confirmed during the Stage 1c rollout (2026-10-05 → 07):
  headless runs of the desktop app's Claude Code 2.1.286–2.1.289 loaded 0 of 6 core rules in
  devpulse, shotsmith and c3d, while Xcode-hosted 2.1.154 still followed the links.
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
- **The launcher holds no secrets (2026-10-27).** It asks only for the Team ID, GitHub org
  and domain, because bootstrap.sh reads only `TEAM_ID` and `ORG`; the ASC Key and Issuer IDs
  come from each project's `.env.fastlane` and GitHub Secrets. Each run restores or removes
  the `.env.playbook`/`.env.project` it writes, and loading drops the ASC IDs older builds
  kept in `UserDefaults`. Git history has never held a `.env.*` or `.p8` file. The `.p8` ASC
  key is still the crown jewel: rotate it if it's ever committed.
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
- **Paid agent tools (eval 2026-10-22):** Codex stays as the merge reviewer; Cursor ($20 legacy Pro) stays for now while a Grok Bot job comes up on its own; Bitrig gets a greenfield test against the playbook by 2026-11-07 (`~/dev/tool-eval-2026-11/decision.md`).

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
  symlink in devpulse / shotsmith / c3d-bridge-modeler now serves the cleaned rule *(since Stage
  1c, those three carry the core as a rendered `AGENTS.md` block instead)*. CHANGELOG entry
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
      tests, c3d declares no runner), so neither has `/test` until then. **Update 2026-10:** both
      were re-bridged in Stage 1c (devpulse #2, c3d #22) and have `/test`; c3d now declares
      `python3 -m pytest -q test` (201 passed).
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
- [~] **Autonomy policy (2026-10-22), decision Auto in §2.** The aim is to stop per-step
  approvals for routine, reversible work, with auto mode, a few native rules and short core
  rules. The proposal stays local (`AUTONOMY-PROPOSAL-2026-10.md`, untracked).
  - [x] PR 1, the policy text: #41 → `90fb81e`.
  - [x] PR 2 (#43 → `85a165d`) and sandbox exemptions (#44 → `26cf2ac`). The canary broke
    push, `gh`, `simctl` and pytest inside the sandbox, so the settings were rolled back.
  - [x] Lean cleanup (#45 → `e3c04f0`): the sandbox, guard, installer and word list are gone;
    `PLAYBOOK_AUTONOMY=on` alone switches autonomy on; one GitHub Codex bot review per PR;
    `codex-review.sh` stays as a second opinion during development.
  - [x] flara-web gets `autonomy: off` (flara-web #1); flara-app's `AGENTS.md` notes that
    Pages serves `docs/` from `main` (flara-app #70).
  - [x] Owner, once (2026-10-22): the `settings/autonomy.json` rules are in the user settings,
    plus an `autoMode.allow` entry for checklist merges; dry-run pushes confirmed the force-push
    deny rules block and ordinary pushes pass. The old `~/.config/playbook/` copies are deleted,
    and `PLAYBOOK_AUTONOMY=on`.
  - [x] Re-render downstream (2026-10-22): shotsmith, devpulse and c3d-bridge-modeler through
    `bridge-symlink.sh`; teewye-app, broadsheet-app (into `dev`) and flara-app through compose.
    The Codex reviews of those PRs found four fixes, shipped as plugin releases:
    - 1.2.0 (#47): "Second opinions" resolves `PLAYBOOK_HOME`, and `/conform` parks
      STALE_CORE_BLOCK under autonomy;
    - 1.2.1 (#48): `/deploy` and `/release` require a clean tree, restore fastlane's edits,
      and record "Current State" through a `chore/` PR;
    - 1.2.2 (#49) and 1.2.3 (#51): the restore covers only the `.pbxproj` and `Info.plist`
      files fastlane changed, and stops and asks if anything else is still changed.
  - [ ] With the next core change, add two owner-approved rules (2026-10-22) to the merge
    checklist, so one re-render round covers both:
    - **Review fallback.** If the GitHub Codex review hasn't finished within about 15 minutes,
      one local `codex-review.sh` review with the same bar counts as the merge review. Two
      bot reviews stalled for 20–30 minutes on 2026-10-22 while about ten ran at once; #49
      and #51 already used the fallback, and on #51 the local review caught a real bug.
      **2026-10-27:** Erik: use the local review, because the bot has been failing (#60's sat
      at "running" for over two hours). So when this rule lands, word it as "the local review
      is the merge review" rather than a fallback. On #60 the local review caught two real
      bugs in three rounds.
    - **Prose-only PRs.** "A PR that changes only prose outside `AGENTS.md`/`CLAUDE.md`,
      `.claude/`, hooks, workflows and code needs no Codex review; publishing still needs
      the user." The rule goes by path, not by judgment, because instruction files change
      agent behavior even in small edits.
    - **Ride-alongs (2026-10-27 curation):** word the prose-only rule's excluded paths to
      also cover the playbook's `core/` and `packs/` sources, which become downstream
      instructions; and give the inbox entry format one home, the `inbox.md` header, with the
      capture rule, `/inbox` and the core block pointing to it. Captures stay unnumbered
      (`/curate` numbers them), so today's copies of the format still agree.
  - [x] Cleanup: the memory notes are done, and starter prompts carry only the task
    (2026-10-22). The owner's communication preferences moved to a private user-level file
    outside this repo.
- [x] **Maintenance mode (2026-10-22).** The modernization is done. The six opted-in projects
  live in `~/dev`, run on the shared core and packs in the `AGENTS.md` layout, and have
  autonomy on; new projects start the same way (Stage 1c in §4, `.xcode-version` since #53). The playbook
  is no longer a project: its work happens on contact, when a project hits a problem (inbox →
  `/curate`) or a decision has a date. A new idea goes on the on-contact list as one line and
  becomes work only when a project needs it.
  - **On contact** (nothing to do until a project touches it):
    - `.xcode-version` in teewye and broadsheet, which still pin Xcode 26.3 in their
      workflows: copy flara-app #65 the next time either needs a new Xcode.
    - Stage 1b Phase 3–4. teewye and broadsheet still use the pinned submodule; move each to
      the plugin with Flara's recipe (#56) when it's next touched. Then Phase 4: retire the
      composed `/upgrade`, teach `bootstrap.sh`, and wire the tag into `/wrapup`.
      `/playbook:upgrade` is the primary upgrade verb; `/conform` stays the drift check.
    - The two queued merge-checklist rules (Autonomy, above): with the next core change.
    - M0/M1, the toolchain and iOS 27 fact refresh, including iPhone Duo: refresh what a
      project's work needs, when it needs it.
    - Inbox curation: done 2026-10-27 (21 entries: 13 adopted, 7 discarded). #21, the Grok
      hand-off of App Store Connect steps, was adopted 2026-10-28 as the core "Grok Bot"
      section after a session read a Grok Bot request as a Grok chatbot research hand-off.
      The inbox is empty. Run `/curate` when it gets in the way again.
    - 3a, `loadcheck.sh` as a playbook tool: the next time an instructions-loading check is
      needed (`codex-review.sh` landed with autonomy).
    - Phase C's `/context-health` and `/preflight`, as above.
  - **Parked** (restart only with a reason):
    - Stage 2 (re-scoped 2026-06-10): Apple's exported Xcode 27 skills for the overlapping
      ground; Hudson, SHA-pinned, for SwiftData + Concurrency only.
    - Stage 3: Codex + MCP + a bake-off harness. The coding-tool subscription bake-off runs
      as a purchase decision inside project work, not as a playbook stage.
    - Stage 4: the PlaybookLauncher spin-out.

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
