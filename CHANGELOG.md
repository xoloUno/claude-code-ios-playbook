# Playbook Changelog

Recent changes to the iOS project playbook. When starting a Claude Code session in a
project that uses this playbook, read this file to check if the project needs updating.

Each entry describes what changed, which playbook files were affected, and what to do
in your project to adopt the change.

## Superseded-by convention

When a later entry retracts or replaces guidance from an earlier one, the **earlier
entry** gets a one-line banner immediately under its `##` heading:

```markdown
> **Superseded by:** YYYY-MM-DD — <title>. <one-sentence description of what's
> different now and what readers should ignore from this entry>.
```

Use **`Superseded by:`** when the earlier entry is fully retracted (e.g. a tool
or lane has been deleted), and **`Partially superseded by:`** when only some of
the earlier guidance is now stale (e.g. one fix landed in a rule file but other
fixes still apply for un-migrated projects).

This keeps history append-only — important for `/upgrade`'s date-cursor walking
model — while making it impossible for a reader to follow retracted guidance
without seeing the retraction first. Cheap to add at retraction time, very high
signal during multi-version skips.

---

## 2026-05-13 — Wire prose-humanizer into `/wrapup` for release notes and App Store metadata

The downstream `/wrapup` template now invokes the `prose-humanizer` subagent
on `release-notes-draft.md` and `fastlane/metadata/en-US/description.txt`
when either was modified in the session. This catches AI-tells (decorative
adjectives, inflated verbs, significance padding) at the natural choke point
before commit — App Store reviewers and end users both penalize text that
reads obviously AI-written.

Non-English `description.txt` locales are explicitly skipped — they're
translations, and the humanizer doesn't preserve translation accuracy.

**Files affected:**
- `.claude/templates/commands/wrapup.md` — new step 8 invokes the humanizer subagent on touched user-facing prose; existing steps renumbered (8→9, 9→10, etc.)

**What to do in your project:**
- After running `/upgrade` to pull the updated template, your project's `.claude/commands/wrapup.md` will include the humanizer step. Make sure the plugin is installed first: `claude plugin install writing-prose-like-a-human-for-agents@writing-prose-like-a-human-for-agents` (marketplace must be added — see `claude-code-plugins-setup.md` §11).
- If you don't install the plugin, the step is a no-op and the wrap-up flow falls through cleanly.

---

## 2026-05-13 — Prose humanizer pass across playbook docs, rules, commands, and templates

Ran the `writing-prose-like-a-human-for-agents` plugin's `prose-humanizer`
subagent across every prose surface in the playbook. Net change: **-16 lines
across 29 files** (192 deletions, 176 insertions). The pass cuts decorative
adjectives (`complete`, `production-ready`, `seamless`, `vibrant`), inflated
verbs (`leverages`, `showcases`, `serves as`), significance inflation
(`pivotal`, `critical`, `genuinely`), and trailing participial editorializing.
No code blocks, file paths, commands, or technical content were modified.

The playbook now includes the prose humanizer in its recommended Tier 2
plugin list with a `/release` usage hook for downstream projects to clean
their App Store metadata and release notes pre-submission.

**Files affected:**
- 6 top-level docs: `README.md`, `getting-started.md`, `ios-project-playbook.md`, `CLAUDE-TEMPLATE.md`, `claude-code-plugins-setup.md`, `CONTRIBUTING.md`
- 15 rules: every file under `.claude/rules/`
- 6 commands: every file under `.claude/commands/` except `inbox.md` and `status.md` (already lean)
- 2 templates: `.claude/templates/commands/status.md`, `.claude/templates/commands/wrapup.md`

**What to do in your project:**
- Newly-bootstrapped projects pick up the cleaner prose automatically.
- Existing projects: optional. Run `/upgrade` to pull the latest rule files into your project if you want the consistent prose. No behavior changes — the rules' substance is identical, only the surrounding prose is tightened.
- Adopt the humanizer in your own workflow: install via `claude plugin install writing-prose-like-a-human-for-agents@writing-prose-like-a-human-for-agents` (marketplace must be added first — see `claude-code-plugins-setup.md` §11). Then run `use prose-humanizer on <file>` before App Store metadata submission or any user-facing prose ship.

---

## 2026-05-13 — Plugin/MCP setup refresh: deprecated GH MCP, new plugins, Xcode 26.5

GitHub's `@modelcontextprotocol/server-github` npm package was deprecated and
archived in early 2026; the playbook now points to GitHub's official hosted
server at `https://api.githubcopilot.com/mcp/`. Four new plugins are
documented (Tier 1: `swift-lsp`, `programming-swift-skill`; Tier 2:
`pr-review-toolkit`, `writing-prose-like-a-human-for-agents`). The
`apple-platform-build-tools` marketplace install string was corrected — the
marketplace's internal name (`apple-platform-build-tools`) differs from its
repo slug (`apple-platform-build-tools-claude-code-plugin`), and the prior
example used the slug. Xcode 26.5 agentic features and the XcodeBuildMCP
v2.5 `extraArgs → launchArgs` breaking rename are now flagged.

**Files affected:**
- `claude-code-plugins-setup.md` — GitHub MCP §1 fully rewritten (deprecation note + hosted/Docker install); XcodeBuildMCP §2 version pin dropped, breaking-rename callout added; Apple Platform Build Tools §3 install string and JSON example corrected with explanatory callout; new Tier 1 entries §6 (Swift LSP) and §7 (Swift Programming Language Skill); new Tier 2 entries §10 (PR Review Toolkit) and §11 (Prose Humanizer with `/release` usage hook); "Notable Tool Updates (May 2026)" section added; Betterleaks URL corrected to `betterleaks/betterleaks` (was `AikidoSec/betterleaks`)
- `getting-started.md` — GitHub MCP install command updated to hosted server + deprecation note

**What to do in your project:**
- If `~/.claude/settings.json` references `apple-platform-build-tools@apple-platform-build-tools-claude-code-plugin`, rename the **plugin@marketplace** part to `apple-platform-build-tools@apple-platform-build-tools`. Keep the `repo` URL itself full-length (`kylehughes/apple-platform-build-tools-claude-code-plugin`).
- If you still have the deprecated GitHub MCP installed (`claude mcp list` shows `npx -y @modelcontextprotocol/server-github`), migrate: `claude mcp remove github && claude mcp add --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer $GH_TOKEN"`.
- Optional: install the four new plugins. See `claude-code-plugins-setup.md` §6, §7, §10, §11 for commands.
- Grep your scripts/skills for `extraArgs` — rename to `launchArgs` if you find any (XcodeBuildMCP v2.5 breaking rename). Most projects won't have hits.

---

## 2026-05-05 — `/status` and `/wrapup` tailored to the playbook repo itself

The playbook now ships **two** versions of the `/status` and `/wrapup` slash
commands: one for downstream iOS projects (the existing CLAUDE.md / WORKLOG.md /
MANUAL-TASKS.md flow) and one for the playbook repo itself (a docs/tooling repo
with `CHANGELOG.md` and `inbox.md` instead). Bootstrap continues to emit the
downstream version into new projects — there's no behavior change for any
bootstrapped project.

**Files affected:**
- `.claude/templates/commands/status.md` — new home of the downstream `/status`
  template. Identical contents to the previous `.claude/commands/status.md`.
- `.claude/templates/commands/wrapup.md` — new home of the downstream `/wrapup`
  template. Identical contents to the previous `.claude/commands/wrapup.md`.
- `.claude/commands/status.md` — rewritten as a playbook-specific session
  briefing (branch + `git status` + `CHANGELOG.md` head + `inbox.md` count).
- `.claude/commands/wrapup.md` — rewritten with playbook-specific wrap-up
  steps (CHANGELOG entry rules, branch routing for the playbook's own PRs).
- `bootstrap.sh` — the slash-command copy step now sources from both
  `.claude/commands/` (everything except `curate.md`) and
  `.claude/templates/commands/` (downstream-only variants).

**What to do in your project:**
- Nothing. Re-running `/upgrade` or re-bootstrapping is a no-op for
  `/status` and `/wrapup` content — the templates carry the same instructions
  they did before. This entry exists so a downstream session reading the
  CHANGELOG knows the bootstrap structural change is intentional and inert.

---

## 2026-05-03 — shotsmith spun off to its own repo: `xoloUno/shotsmith`

shotsmith no longer ships in this playbook. It now lives at
[github.com/xoloUno/shotsmith](https://github.com/xoloUno/shotsmith) with its
own release cadence, its own CHANGELOG, and a standalone Claude Code skill.

This is a **clean break** — no transition window, no backward-compat path.
Flara (the only consumer at the time of the split) migrated atomically in
the same release.

### Why now

The earlier `2026-05-03 — appshot retirement` entry settled the question of
"is shotsmith ready?" but kept the in-tree-with-the-playbook install model.
A user-driven re-weigh of the trade-offs landed on three reasons to spin off
ahead of the original "2+ project users" criterion:

1. **Decoupled release cadence** — shotsmith bug fixes ship without waiting
   for a playbook PR window; playbook docs ship without dragging in-flight
   shotsmith state.
2. **Cleaner mental model** — `templates/`, `tests/`, `bin/`, etc. live
   unambiguously in the shotsmith repo. The playbook's role is "tell
   projects how to use shotsmith," not "ship shotsmith."
3. **Standalone Claude Code skill** — `skill/SKILL.md` in the new repo,
   user-installed at `~/.claude/skills/shotsmith/SKILL.md`, gives any
   agent in any project shotsmith awareness with no per-project setup.

The "schema stability for external users" concern that the original criterion
guarded against is mitigated by keeping the new repo private through smoke-test,
and by deferring PyPI publication until a second consumer surfaces.

### What changed in the playbook

**Deleted:**
- `tools/shotsmith/` — entire directory, ~30 files. History preserved in
  the new repo via `git subtree split --prefix=tools/shotsmith`.
- `bootstrap.sh` `# --- shotsmith install (symlink playbook tool into project bin/) ---`
  section — the bootstrap-emitted `bin/shotsmith` symlink to
  `$PLAYBOOK_DIR/tools/shotsmith/bin/shotsmith`.
- `bin/` from the bootstrap-emitted project `.gitignore`.

**Added/updated:**
- `bootstrap.sh` `# --- shotsmith install check ---` section — `command -v
  shotsmith` check that prints a friendly install hint (`pipx install git+...`)
  if shotsmith isn't on PATH. Bootstrap doesn't hard-block on optional tooling.
- `bootstrap.sh` `:compose_screenshots` lane — invokes `shotsmith pipeline`
  from PATH (was `./bin/shotsmith pipeline`); guarded by an
  `unless system("command -v shotsmith")` install-check.
- `ios-project-playbook.md` Phase 5 Track B — install instructions
  switched from "from `tools/shotsmith` in the playbook" to
  `pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0`.
  Project layout diagram drops `bin/shotsmith`.
- `tools/shotsmith/templates/...` references in Phase 5 Track B switched
  from local relative paths to GitHub URLs in the new repo.

### What changed in the new shotsmith repo

(Documented in the standalone repo's `CHANGELOG.md`; summarized here for
playbook readers.)

- `LICENSE` file (MIT — license already declared in pyproject.toml).
- `pyproject.toml` enriched with `[project.urls]` and PyPI classifiers
  (Beta, MIT, macOS, Python 3.9-3.12, Multimedia/Graphics, Build Tools).
- Standalone `CHANGELOG.md` seeded with v0.2.0 release notes.
- `skill/SKILL.md` — Claude Code skill mirroring the frames-cli pattern.
- `.github/workflows/test.yml` — pytest CI on macos-latest × Python 3.10/3.11/3.12.
- README softened (5 playbook-specific references re-framed for a
  general audience).

### To adopt in your project

1. **Pull the playbook via `/upgrade`** — the bootstrap symlink section is
   gone, and `:compose_screenshots` now invokes `shotsmith` from PATH.
2. **Install shotsmith on the machine** (one-time):
   ```bash
   pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0
   ```
3. **(Optional) Install the Claude Code skill:**
   ```bash
   git clone https://github.com/xoloUno/shotsmith.git ~/Code/shotsmith   # if not already
   mkdir -p ~/.claude/skills/shotsmith
   ln -s ~/Code/shotsmith/skill/SKILL.md ~/.claude/skills/shotsmith/SKILL.md
   ```
4. **If your project hardcodes `tools/shotsmith/bin/shotsmith` or
   `./bin/shotsmith`** in its Fastfile or scripts, replace with `shotsmith`
   on PATH. Add an install-check that surfaces the pipx hint on miss.
5. **Re-run `bundle exec fastlane compose_screenshots`** — should produce
   byte-identical output to the previous in-tree shotsmith. If it doesn't,
   `shotsmith verify --config <path>` will name the cause.

### Repo visibility

`xoloUno/shotsmith` started private and flips to public after Flara's
end-to-end smoke test passes. By the time you see this CHANGELOG entry on
main, the repo should be public.

---

## 2026-05-03 — shotsmith 0.2.0: `manual_inputs` config block + Superseded-by convention + vestigial lane cleanup

> **Superseded by:** 2026-05-03 — shotsmith spun off to its own repo: `xoloUno/shotsmith`. The `tools/shotsmith/` directory referenced by this entry no longer exists; install shotsmith via `pipx install git+...` instead. Capability surface (manual_inputs, stage step, `shotsmith stage` subcommand, the verify-end-to-end win) is preserved verbatim in the standalone repo's v0.2.0 release.

Three follow-ups from the Phase 6 wrap-up landed together. All three came
out of the same `/curate` pass on `inbox.md` plus the user's call-out that
the inbox's `manual_inputs` deferral was worth promoting now for the
end-to-end `verify` benefit.

### 1. shotsmith **0.2.0** — `manual_inputs` config block + `stage` step + `stage` subcommand

The `manual_inputs` config block declares which manual-gesture captures
(Live Activity, Home Screen widget, Control Center) shotsmith should stage
into `raw/` before framing. It replaces the per-project Fastfile staging
block (`~10 lines of Ruby in :compose_screenshots`) with a single
source-of-truth in `shotsmith/config.json`:

```json
"manual_inputs": {
  "iphone": {
    "source": "../manual-captures/{locale}",
    "files": [
      "90_LockScreen_LiveActivity.png",
      "91_HomeScreen_Widget.png",
      "92_ControlCenter.png"
    ]
  }
}
```

**Why now (the user's question):** the verify-end-to-end win. Without
`manual_inputs`, a missing manual capture surfaces only via `input_mapping`
indirection in the frame step ("source X.png not found in raw/"). With
`manual_inputs` declared, `shotsmith verify` names the missing source file
directly:

```
❌ iphone/es-MX: manual_inputs source(s) missing in
   /…/manual-captures/es-MX: 91_HomeScreen_Widget.png
```

Concretely shipped:

- `shotsmith/config.py` — new `ManualInputs` + `ManualInputDevice`
  dataclasses; `manual_inputs` parsed and validated at config load
  (string/list/non-empty/required-field checks); `Config.manual_source_dir(device, locale)`
  helper.
- `shotsmith/stage.py` (new, ~110 lines) — `stage_locale()` copies declared
  files from `<source>/<file>` into `<raw_dir>/<file>` per (device, locale).
  Returns `StageResult` with written + skipped lists. Skipped reasons name
  missing source files specifically. No-op when `manual_inputs` isn't
  configured.
- `shotsmith/pipeline.py` — `VALID_STEPS` now `("capture", "stage", "frame", "compose")`;
  `DEFAULT_STEPS` now `("stage", "frame", "compose")`. Stage runs after
  capture (if invoked) and before frame. Aborts pipeline with
  `PipelineError` if any declared source file is missing.
- `shotsmith/__main__.py` — new `shotsmith stage --config X` subcommand
  with `--dry-run`. Prints `ℹ️ No manual_inputs declared in config — stage is a no-op.`
  when not configured.
- `shotsmith/verify.py` — declares a hard error for each missing
  `manual_inputs` source (file or whole dir). Also flagged when
  `pipeline.verify_strict: true`, so a bad config aborts pipeline before
  any work.
- `tests/test_stage.py` (new) — 9 tests covering staging, dry-run,
  missing-source reporting, locale template expansion, multi-device
  no-ops, and config validation rejection paths.
- `tests/test_verify.py` — 3 new tests for `manual_inputs` source-missing
  errors.
- `tests/test_pipeline.py` — 3 new tests for stage step ordering, abort on
  missing source, and `DEFAULT_STEPS` regression guard.
- `templates/config.example.json` — bumped to demonstrate `manual_inputs`.
- `tools/shotsmith/README.md` — new "Manual inputs" subsection + updated
  Usage section listing 5 subcommands (was 4).
- VERSION / pyproject.toml / `__init__.py` — bumped to 0.2.0.

**Test count:** 67 → 83 (16 new). All pass.

### 2. `bootstrap.sh` — `:compose_screenshots` simplified, vestigial lanes deleted

The bootstrap-emitted `:compose_screenshots` lane no longer has its own
staging logic — it's now a one-line wrapper around `./bin/shotsmith pipeline`
(staging is shotsmith's job via the `manual_inputs` block). Error message
points the user at `shotsmith verify` for diagnostics.

Two vestigial fastlane lanes deleted (~25 lines):

- `:screenshots` — ran XCUITest then called `frame_screenshots`. Wrote to
  the old flat `<locale>/*_framed.png` layout that doesn't match shotsmith
  v2's `<locale>/<device>/raw/` contract. Projects on shotsmith write a
  project-specific `scripts/capture-screenshots.sh` instead.
- `:frame_screenshots` — wrapped `frames -o <dir> <dir>*.png` in the same
  flat layout. Replaced by shotsmith's `frame` step which handles the
  per-device subdir contract.

Lanes remaining: `:beta`, `:release`, `:widget_screenshots`,
`:compose_screenshots`, `:upload_metadata`, `:upload_screenshots`. The
`:widget_screenshots` lane lost its trailing `frame_screenshots` call but
otherwise stayed (still useful for projects driving widget capture via
simctl scripts; new projects should prefer `/capture-manual-surfaces`).

### 3. Superseded-by banner convention + 3 backfilled entries

Adopted from a 2026-05-03 Flara `/curate` finding that walking 8 days of
CHANGELOG entries surfaced three already-retracted items.

- New section **"Superseded-by convention"** in CHANGELOG.md header
  documents the syntax (`> **Superseded by:** YYYY-MM-DD — <title>. <one
  sentence>.`) and the `Partially superseded by:` variant.
- Banners backfilled on three stale entries:
  - **2026-04-27 — Track B replaced: appshot-cli + Apple Frames CLI** →
    superseded by today's appshot retirement.
  - **2026-04-26 — Screenshot pipeline hardening** → partially superseded
    by the 2026-05-03 rule files (`status-bar-overrides.md`,
    `screenshot-pipeline.md`).
  - **2026-04-25 — Control Center capture lane (Quartz drag)** →
    superseded by 2026-05-03 agent-driven manual-capture loop.

**Why this matters:** `/upgrade`'s date-cursor model walks CHANGELOG
entries forward from the project's `.playbook-version`. A project on a
multi-version skip would otherwise silently follow retracted guidance
(install appshot-cli, wire up Quartz drag) before being told to remove it
days later. The banner makes the retraction visible in the same pass.

### 4. Inbox curation

Three entries from `inbox.md` processed:

- **adopted** — 2026-05-03 Playbook (deferred shotsmith CLI work) →
  `manual_inputs` shipped (item 1 above).
- **adopted** — 2026-05-03 Flara (Superseded-by banner) → convention +
  backfill shipped (item 3 above).
- **deferred** — 2026-04-27 HVACApp internal/team archetype + parallel-tasks
  worktree workflow. Both are sizable doc/scaffold additions worth their
  own focused session.

**To adopt in your project:**

1. Pull via `/upgrade` (no manual steps needed for the core update —
   shotsmith updates automatically via the `bin/shotsmith` symlink).
2. **If your project has a `:compose_screenshots` Fastfile lane that
   stages manual-captures via Ruby:** simplify it to the one-line wrapper
   shown in `bootstrap.sh`. Add a `manual_inputs` block to your
   `fastlane/shotsmith/config.json` matching the surfaces you have. Run
   `./bin/shotsmith verify --config fastlane/shotsmith/config.json` to
   confirm the new contract before recapturing.
3. **If your project has `:screenshots` and/or `:frame_screenshots`
   lanes:** delete them — your `:compose_screenshots` lane already
   handles the framing step via shotsmith. Keep your project-specific
   `scripts/capture-screenshots.sh` (or equivalent) for the XCUITest
   capture step.

---

## 2026-05-03 — appshot retirement + watch composition cleanup (Phase 6 finished)

**What changed:** Closes out Phase 6 of the long-running shotsmith plan
(`thank-you-so-much-drifting-cocoa.md`) by finishing the appshot retirement
and aligning the playbook's watch-screenshot rule with what Flara actually
ships. Three files touched.

### 1. `bootstrap.sh` — appshot scaffolding deleted, shotsmith install wired

- **Deleted** the entire `# --- appshot-cli scaffolding (Track B …)` section
  (~99 lines) — `fastlane/appshot/.appshot/config.json`, the iPhone/iPad
  caption JSON skeletons, the `mkdir -p fastlane/appshot/{screenshots,…}`
  scaffolding, and the bootstrap-emitted `scripts/patch-appshot.sh` (the
  22-line monkey-patch that bumped appshot v2's caption font-size cap).
- **Deleted** the `appshot — keep config + captions` `.gitignore` block
  (`fastlane/appshot/screenshots/`, `fastlane/appshot/final/`,
  `fastlane/appshot/.appshot/config.backup.json`).
- **Deleted** the `:appshot_screenshots` fastlane lane (~36 lines —
  staged `_framed.png` siblings into the appshot input dir, ran
  `appshot build --no-frame --langs <lang>`, copied output back).
- **Added** a `# --- shotsmith install (symlink playbook tool into project bin/) ---`
  section. Bootstrap now creates `bin/shotsmith` as a symlink to
  `$SCRIPT_DIR/tools/shotsmith/bin/shotsmith` so the
  `:compose_screenshots` lane's `./bin/shotsmith pipeline` invocation works
  out of the box. Symlink rather than copy means projects pick up shotsmith
  updates automatically when `/upgrade` syncs the playbook.

### 2. `ios-project-playbook.md` Phase 5 Track B — full rewrite

The "Track B — appshot-cli + Apple Frames CLI" subsection (~148 lines —
two-CLI pipeline diagram, `npm install -g appshot-cli` + `patch-appshot.sh`
install, `fastlane/appshot/` directory layout, the `parseFontName` `Bold`
suffix gotcha, the `:appshot_screenshots` lane invocation per locale) is
**replaced** with "Track B — shotsmith (when you need captions + gradients
+ multi-locale)". The new section:

- Points at `.claude/rules/screenshot-pipeline.md` as the durable contract
  (two-input-tree pattern, four artifact layers, agent-driven manual
  capture loop, watch checklist) — that rule auto-loads in any project.
- Documents the shotsmith install (`pip install -r requirements.txt` once;
  bootstrap symlinks `bin/shotsmith`).
- Walks the new directory layout with `fastlane/manual-captures/` tracked
  vs. `fastlane/screenshots/` regenerable.
- Shows the v2 `config.json` schema (subtitle, dither, `input_mapping`,
  per-device overrides) and points at the three bundled gradient presets
  (`mauve`, `royal-purple`, `apple-music`).
- Replaces the per-locale `appshot_screenshots` invocation with the
  single-shot `bundle exec fastlane compose_screenshots` lane (multi-locale
  in one pass).
- Explicitly calls out **watch is screen-only** — ASC submissions are raw
  `simctl io screenshot` output with no framing/gradient/caption (Path 1;
  the watch hardware corner-radius would clip the art anyway).

The "Recommended Workflow by Project Stage" table (Phase 5) drops the
"Caption / Background" column and merges it into "Frame + Caption +
Background", with the marketing-heavy row pointing at
`fastlane compose_screenshots` (Track B / shotsmith) instead of
`appshot_screenshots`.

### 3. `.claude/rules/screenshot-pipeline.md` — watch section aligned to Flara reality

- **Intro paragraph** rewritten to declare ASC watch submissions are
  screen-only PNGs from `simctl io screenshot` (no bezel, no gradient, no
  caption), citing Flara v2.1 (2026-04-28) production verification: Apple
  accepted the framed upload, but the watch hardware's display
  corner-radius clipped the gradient and caption corners at viewing time.
- **Gotcha #1** ("composed marketing PNG must be at exact size") reframed
  for direct simctl output (no scaling, no padding).
- **Gotcha #3** flipped — the answer is now "don't frame on the ASC path"
  (frames-cli's bezels include strap; the hardware corner-radius would clip
  added art anyway), not "draw the bezel directly in ImageMagick."
- **`scripts/compose-watch-marketing.sh` subsection** (~85-line
  ImageMagick recipe — concentric titanium ring + black inner ring +
  gradient + caption at 422×514) removed entirely. Replaced with a short
  "Staging into the composed-output dir" subsection showing the ~5-line
  Ruby snippet that stages raw watch PNGs into the composed-output tree
  alongside iPhone/iPad so a single `upload_screenshots` ships everything.

**Net diffstat:** ~290 lines deleted, ~210 lines added across the three
files. Bootstrap leaves projects with a working `compose_screenshots`
pipeline cold; the appshot scaffolding is gone for good.

**Why now:** The shotsmith tool itself shipped 2026-04-27 and Flara
migrated to it on the same date. The playbook's bootstrap and Phase 5 doc
got partially updated but kept the appshot scaffolding alongside the new
shotsmith lane — a freshly-bootstrapped project ended up with both, with
appshot as the documented Track B path while shotsmith hung in the air.
This entry retires the dead scaffolding so new projects get shotsmith by
default and don't have to discover the migration.

**To adopt in your project:**

1. Pull via `/upgrade`. New `bin/shotsmith` symlink will appear; updated
   `ios-project-playbook.md` Phase 5 Track B will be visible in the
   playbook checkout.
2. **If your project still has appshot scaffolding** (likely if it was
   bootstrapped before 2026-05-03):
   - `git rm -rf fastlane/appshot/`
   - `git rm scripts/patch-appshot.sh`
   - Remove the `appshot — keep config + captions` block from your
     project `.gitignore`.
   - Remove the `:appshot_screenshots` lane from your `fastlane/Fastfile`.
   - `npm uninstall -g appshot-cli` (optional cleanup).
   - Migrate captions: translate `fastlane/appshot/.appshot/captions/*.json`
     into `fastlane/shotsmith/captions.json` (schema in the playbook §Phase 5
     Track B and `tools/shotsmith/README.md`). Translate the gradient/font
     from `.appshot/config.json` into `fastlane/shotsmith/config.json`.
   - Add `mkdir -p bin && ln -sfn /path/to/_playbook/tools/shotsmith/bin/shotsmith bin/shotsmith`
     if your bootstrap predates 2026-05-03.
3. **If your project never adopted appshot:** the new symlink is the only
   change; the bootstrap `:compose_screenshots` lane already targets
   shotsmith.

**Project-side reference for the migration:** Flara's commit history
between 2026-04-27 and 2026-05-03 has the full migration recipe — search
the commits referencing `compose-watch-marketing.sh` deletion and the
shotsmith pipeline cutover.

---

## 2026-05-03 — Agent-driven manual-capture pipeline + Control Center retirement

**What changed:** The screenshot pipeline now formally documents a **two-input-tree
pattern** with four artifact layers, replaces the unreliable Quartz-drag Control
Center automation with an **agent-driven loop**, and ports the watch screenshot
pipeline. Three new files plus targeted bootstrap and Phase 5 edits.

### 1. New rule — `.claude/rules/screenshot-pipeline.md`

The canonical reference for App Store screenshot pipelines. Covers:

- **The two-input-tree pattern** — split inputs into `fastlane/manual-captures/`
  (tracked, "once per release" manual-gesture inputs) and
  `fastlane/screenshots/<locale>/<device>/raw/` (gitignored, regenerable XCUITest
  output). Solves three problems at once: small git history, versionable manual
  inputs, legible cadence intent.
- **The four artifact layers** — `manual-captures/` + XCUITest `raw/` →
  `framed/` → `composed/`.
- **The agent-driven capture loop** — Claude Code runs the prep (boot, locale,
  status bar, app launch) and the user performs Simulator gestures and types
  `ready` in chat between surfaces. Sidesteps `read -p`'s EOF-on-stdin issue
  and is more reliable than scripted Quartz drag.
- **Surface gesture inventory** — Live Activity (`90_LockScreen_LiveActivity`),
  Home Screen widget (`91_HomeScreen_Widget`), Control Center (`92_ControlCenter`).
- **Inlined fallback script** (`scripts/capture-manual-surface.sh`) for
  non-Claude-Code workflows.
- **Watch capture checklist** with the seven gotchas (ASC dimensions per device
  class, alpha rejection requiring `PNG24:` ImageMagick prefix, frames-cli
  bezels include band/strap so use ImageMagick concentric rings instead, sheet
  auto-presentation needing a deferred `Task.sleep(for:)`, ScrollViewReader
  scroll-to races, demo-data shape per screen, locale switching is per-launch-arg).
- Inlined `scripts/capture-watch-screenshots.sh` and
  `scripts/compose-watch-marketing.sh` using `WATCH_SIM` from `.env.project`
  (never hardcoded sim model name).

### 2. New slash command — `.claude/commands/capture-manual-surfaces.md`

Drives the agent-driven loop end-to-end. Reads `.env.project` and
`shotsmith/config.json`, walks each (locale × surface) pair, prepping the
simulator and capturing on the user's `ready` cue. Lenient parsing
(`ready`/`done`/`go`/`ok` advance; `redo`/`back`/`skip`/`cancel` for control
flow). Verifies each PNG exists and is non-empty before advancing.

### 3. Bootstrap.sh edits

- **Deleted** the entire `cat > fastlane/capture_control_center.sh << 'CAPTURECC'`
  heredoc (~110 lines of Quartz-drag automation that was unreliable across
  machines and accessibility-permission states). Bootstrap stops emitting this
  script.
- **Deleted** the `:control_center_screenshot` Fastfile lane.
- **Added** a `:compose_screenshots` Fastfile lane that stages
  `fastlane/manual-captures/<locale>/` into the iPhone `raw/` tree, then runs
  `./bin/shotsmith pipeline`. shotsmith's `input_mapping` renames the `90/91/92_`
  prefixes to canonical caption names.
- **Added** `fastlane/manual-captures/README.md` emission — a discoverability
  doc that explains what lives there, when to recapture, the "once per release"
  cadence, and how the compose lane stages files.
- **Updated** the emitted `.gitignore` to ignore `fastlane/screenshots/` and
  `fastlane/shotsmith/composed/` with an explicit comment line above declaring
  `fastlane/manual-captures/` is **intentionally tracked**.

### 4. Phase 5 update — `ios-project-playbook.md` Step 2.6

Replaced the entire "Control Center Capture (Control Widget apps only)"
subsection (~75 lines of Quartz-drag setup, Accessibility-permission
prerequisites, and troubleshooting table) with a much shorter "Manual-capture
surfaces" subsection that directs to the rule + slash command, calls out the
opt-in nature of this step (apps without LA / widgets / Control Widget skip
it), and documents the `compose_screenshots` lane.

### 5. Inbox curation

Removed the **2026-04-28 Flara watch pipeline entry** (lines 105–170 — the
seven-gotcha watch checklist, now inlined in `screenshot-pipeline.md`) and the
**2026-05-03 Flara two-input-tree entry** (lines 172–247 — the directory
naming + README discoverability suggestions, all adopted). Replaced with a
small deferred entry naming two shotsmith CLI changes (mirror subcommand;
`manual_inputs` config block) flagged for a future shotsmith-focused session.

**To adopt in your project:**

1. Pull via `/upgrade`. New rule (`screenshot-pipeline.md`) and slash command
   (`/capture-manual-surfaces`) propagate automatically.
2. **If your app ships a Live Activity, Home Screen widget, or Control Widget:**
   - Decide whether to migrate to the new flow now or defer.
   - To migrate now: `git rm fastlane/capture_control_center.sh` (the old
     Quartz-drag script — bootstrap no longer emits it). `mkdir -p
     fastlane/manual-captures` (or re-run bootstrap to get the README).
     Run `/capture-manual-surfaces` to recapture into the new directory.
     Update your `.gitignore` per the comment block in the rule. Add a
     `:compose_screenshots` lane to your Fastfile (template in bootstrap.sh).
   - Move existing `fastlane/screenshots/<locale>/iPhone 6.9" Display/9*_*.png`
     captures into `fastlane/manual-captures/<locale>/` to preserve them.
3. **If your app has no manual-gesture surfaces:** ignore — no action needed.

---

## 2026-05-03 — shotsmith 0.1.1: Pillow diagnostic

**What changed:** `tools/shotsmith/bin/shotsmith` now catches a missing-Pillow
`ImportError` and prints the exact `pip install` command for the active Python
interpreter, instead of letting a raw traceback bubble up. Sourced from
`requirements.txt` so the version pin stays in one place. Also bumped to
`0.1.1` (in `__init__.py`, `pyproject.toml`, and `VERSION`) and added a
**Requirements** section to the shotsmith README.

**Why:** Stock macOS resolves `python3` to `/usr/bin/python3` (3.9), which does
**not** ship with Pillow. A fresh-Mac contributor running `./bin/shotsmith`
hits an `ImportError: No module named PIL` traceback with no obvious next step.
The friendly diagnostic identifies the active Python explicitly and prints a
copy-paste-ready install command.

**To adopt in your project:** `/upgrade` will pull the new shotsmith. No
project-side change required.

---

## 2026-05-03 — New rule: status-bar overrides

**What changed:** New `.claude/rules/status-bar-overrides.md` documents the canonical
`xcrun simctl status_bar override` block that every screenshot-capture script must run
before launching the target app, and explains *why* each of the seven flags exists
(`--time "9:41"`, `--dataNetwork hide`, `--batteryState charged`, `--batteryLevel 100`,
`--cellularBars 4`, `--wifiBars 3`, `--operatorName ""`).

**Why:** A downstream session refactored capture scripts in a single commit and silently
dropped `--operatorName ""` and `--dataNetwork hide` from all of them. The drop wasn't
caught for weeks because the captures still rendered — just with "Carrier" visible in
the status bar and the Control Center status row wrapping to two rows. By the time it
surfaced, those flags had to be re-added across multiple scripts. The new rule
documents the flags' rationale so the next refactor leaves them alone.

**To adopt in your project:**

1. Pull the new rule via `/upgrade`.
2. If you've recently refactored any `fastlane/capture_*.sh` or
   `scripts/capture-*.sh` script, audit it against the canonical block in the rule.
3. Re-capture one screenshot per script and verify: 9:41, no carrier name, no 5G/LTE
   label, full bars on both icons, full battery + lightning bolt. For Control Center
   specifically, confirm the Wi-Fi icon stays on the same row as cellular.

---

## 2026-04-28 — Inbox curation: assertion discipline, legal URLs, ASC troubleshooting, Fastfile UTF-8

**What changed:** Four playbook adoptions from the 2026-04-28 inbox triage. Three new
`.claude/rules/` files plus a defense-in-depth `before_all` block in the bootstrapped
Fastfile template.

### 1. New rule — `.claude/rules/assertion-discipline.md`

Extends the auto-memory "Before recommending from memory" discipline (which covers code
paths and feature flags) to higher-stakes claim categories: **App Store rendering rules**
(e.g. watch screenshots are NOT rendered inside a stylized watch frame), **repo
visibility / GH Pages tier** (run `git remote -v` + `gh repo view --json visibility`
before recommending public/private toggles), **fastlane / ASC operational behavior**,
and **simulator capabilities**. Includes the concrete verification commands for each
category. Triggered by a planning session where two factual mistakes (claiming watch
screenshots get an automatic stylized frame; suggesting a private→public repo toggle to
"fix" Pages, which would have exposed all source) landed in quick succession from
training-memory recall.

### 2. New rule — `.claude/rules/legal-urls.md`

Single-source-of-truth pattern for privacy/terms/marketing/support URLs across Swift
code AND fastlane metadata. Two pieces:

- `<App>/Configuration/LegalURLs.swift` — `enum LegalURLs { static let base = ... }`
  referenced from every SwiftUI view.
- `scripts/update-legal-urls.sh` — idempotent migration script that takes a base URL
  and rewrites the Swift constant plus every locale's `privacy_url.txt`,
  `marketing_url.txt`, `support_url.txt`, **and embedded privacy/terms links inside
  `description.txt`**.

The `description.txt` rewrite is the key insight — privacy/terms links embedded inline
in the app description need to stay in sync with the dedicated URL fields, or ASC review
can flag a broken privacy link in the description. The `sed` pattern matches only URLs
ending in `/privacy.html` or `/terms.html`, so Apple's EULA URL and unrelated marketing
links are untouched.

Reference implementation in Flara: `Flara/Configuration/LegalURLs.swift` +
`scripts/update-legal-urls.sh`.

### 3. New rule — `.claude/rules/asc-troubleshooting.md`

Documents the **fastlane screenshot verify hang** — `fastlane upload_screenshots` (or
`release` with screenshots) appears to hang for tens of minutes after all files have
already uploaded successfully because ASC's verify endpoint returns 500 transiently
during high-load periods. Fix: kill the lane, run a direct ASC API query to confirm
state. Includes a `scripts/asc-query.rb` helper (~30 lines, JWT-signed) and bash
wrapper for general-purpose ASC sanity checks (build state, version state, screenshot
sets, etc.).

### 4. Fastfile template — `before_all` UTF-8 hook (`bootstrap.sh`)

Added to the bootstrapped `fastlane/Fastfile` template as defense-in-depth:

```ruby
before_all do
  ENV["LC_ALL"] ||= "en_US.UTF-8"
  ENV["LANG"] ||= "en_US.UTF-8"
  ENV["LANGUAGE"] ||= "en_US.UTF-8"
end
```

The `/deploy` and `/release` slash commands already prepend `LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8`
exports, and `ios-project-playbook.md` §1.5 + §1.6 document this. The `before_all` block
ensures lanes invoked directly (without the slash command's wrapper) don't crash with
`invalid byte sequence in US-ASCII` from gym's error handler.

**To adopt in existing projects:**

1. Re-bootstrap or copy the three new rule files into `.claude/rules/`:
   - `assertion-discipline.md`
   - `legal-urls.md`
   - `asc-troubleshooting.md`
   (Or run `/upgrade` once it picks up this CHANGELOG entry.)
2. For the Fastfile UTF-8 hook: add the `before_all` block above to your project's
   `fastlane/Fastfile`, just below `default_platform(:ios)`. Optional but cheap.
3. For the legal-URLs pattern: opt-in. If your app has hosted legal pages, follow
   `legal-urls.md` to extract `LegalURLs.swift` + the update script. Use the Flara
   implementation as reference.
4. For the ASC query helper: opt-in. If you've hit the screenshot-verify hang or want
   to script ASC checks, drop `scripts/asc-query.rb` from the rule into your project.

---

## 2026-04-27 — `/conform` slash command (full-state playbook audit)

**What changed:** New `/conform` slash command lives at
`_playbook/.claude/commands/conform.md` and gets copied into every newly bootstrapped
project by the existing copy loop in `bootstrap.sh` (lines 1336–1342). Bootstrap.sh
needs no changes — the loop already picks up any `.md` file in
`_playbook/.claude/commands/` except `curate.md`.

`/conform` complements `/upgrade`: where `/upgrade` is delta-driven (replays CHANGELOG
entries since the last `.playbook-version` date), `/conform` is state-driven (directly
compares the project's current shape against the playbook source, regardless of
CHANGELOG history). Use it when CHANGELOG entries may have been missed, after a long
absence, or when adopting the playbook on an existing project.

**Audit categories (six checks):**

1. **Stale playbook-copied rule files** (`.claude/rules/*.md`) — diff against playbook
   source, accounting for `PLAYBOOK_PATH` and `PRIMARY_SIM` substitutions. Auto-fixable.
2. **Stale playbook-copied commands** (`.claude/commands/*.md`, excluding `curate.md`) —
   diff against playbook source. Auto-fixable.
3. **Missing bootstrap-emitted commands** — checks for `feature`, `test`, `review`,
   `deploy`, `release`, `preflight`. Manual fix only (heredoc context not reproducible
   from `/conform`).
4. **CLAUDE.md template gaps** — H2 sections present in `CLAUDE-TEMPLATE.md` but absent
   from project's `CLAUDE.md`. Advisory only — never auto-edits CLAUDE.md.
5. **Doc bloat** — presence of `MILESTONES.md`, `FEEDBACK.md`, or `SESSION-*.md` /
   `LOG-*.md` patterns at project root. Advisory; points to Appendix C migration
   walkthrough.
6. **Stranded `.claude/` files** — files in project's `.claude/rules/` or
   `.claude/commands/` that aren't in playbook source AND aren't bootstrap-emitted
   commands. Advisory — could be intentional custom keepers.

**Appendix C updated:** the "Future: `/conform` slash command (roadmap)" subsection in
`ios-project-playbook.md` is replaced with the active "`/conform` slash command
(full-state audit)" describing the actual command behavior.

**To adopt in existing projects:**

1. Copy `<playbook>/.claude/commands/conform.md` into your project's
   `.claude/commands/conform.md`, OR re-bootstrap a fresh project and copy the file
   from there.
2. Run `/conform` to perform the first audit. Recommended order: `/upgrade` first
   (CHANGELOG-driven), then `/conform` (state-driven catch-all).

---

## 2026-04-27 — Inbox curation: Control Widget intents, PRIMARY_SIM, SwiftData tests, migration appendix

**What changed:** Four playbook adoptions from the 2026-04-27 inbox triage:

1. **Control Widget intent pattern** — new §4.5 in `ios-project-playbook.md` covering
   the App Group bridge for `AppIntent`-backed Control Widgets on iOS 26. The
   `OpensIntent(OpenURLIntent(...))` return path silently drops the URL; use a shared
   App Group UserDefaults handoff instead. One-line cross-reference added to
   `.claude/rules/wwdc25-ios26.md`.

2. **`PRIMARY_SIM` env var** — `bootstrap.sh` now reads `PRIMARY_SIM` from
   `.env.project` (default `iPhone 17 Pro`) and substitutes it into the GitHub Actions
   build destination, the emitted `preflight.md`, and (via post-cp sed) the build-deploy
   and testing rule files. Lets iPad-first projects bootstrap with
   `PRIMARY_SIM=iPad mini (A17 Pro)` without manual edits. Screenshot device list
   (Snapfile) is unchanged because ASC submission requirements are project-independent.

3. **SwiftData test target gotcha** — new "SwiftData test target setup" subsection in
   `.claude/rules/testing.md`. Shared `@Model` files compiled into both the host app
   AND the test bundle (when `TEST_HOST` is set) crash SwiftData on first
   `context.insert(...)` because the same Swift type exists twice in one process.
   Use `@testable import` only.

4. **Migration appendix** — new Appendix C in `ios-project-playbook.md` walking through
   the five-step consolidation pass for projects adopting the playbook later. Existing
   "Maintaining the Playbook" appendix renumbered to D; "Glossary" renumbered to E.
   Includes a roadmap note for the future `/conform` slash command (full-state audit
   complementing `/upgrade`'s delta-driven model).

**Bootstrap-emitted artifacts (changed):**
- `.env.project.example` — adds `PRIMARY_SIM` line
- `bootstrap.sh` — fallback default + three substitutions for `PRIMARY_SIM`

**To adopt in existing projects:**

1. Run `/upgrade` to refresh `.claude/rules/{wwdc25-ios26,testing}.md`.
2. If your project is iPad-first or multiplatform, set `PRIMARY_SIM` in your
   project's `.env.project` and re-run any rule-file refresh.
3. If your project ships a Control Widget backed by an `AppIntent`, audit your intent
   return values for `OpensIntent(OpenURLIntent(...))` and migrate to the App Group
   bridge per §4.5.

---

## 2026-04-27 — `/preflight` slash command + `verify-review` user-level skill

**What changed:** Two new agent affordances to address recurring friction surfaced by
`/insights`:

1. **`/preflight` slash command (project-emitted)** — Pre-deploy gate that validates
   simulator availability, ASC metadata character limits, metadata field completeness
   per locale, git state, marketing version, and build number *before* `/deploy` or
   `/release` runs. Catches the recurring trio of foot-guns (missing simulators,
   char-limit overflows, forgotten `promotional_text`) before kicking off a long
   build/upload cycle.

2. **`verify-review` user-level skill (global)** — Forces grep-before-classify on every
   external review finding (Codex output, lint reports, gh PR review comments, security
   scan results). Each finding gets verified against the actual codebase and classified
   `TRUE_POSITIVE` / `FALSE_POSITIVE` / `NEEDS_INFO` with evidence; no edits are made
   until the user approves the classification. Lives at
   `~/.claude/skills/verify-review/SKILL.md` so it activates across every repo, not
   just iOS projects.

**Bootstrap-emitted artifacts (new):**

- `.claude/commands/preflight.md` — heredoc in `bootstrap.sh` next to `deploy.md` and
  `release.md` (project-specific because it depends on the `fastlane/metadata/` and
  `project.yml` paths).
- `.claude/rules/code-style.md` Slash Commands table updated to list `/preflight`
  between `/review` and `/deploy`.

**To adopt in existing projects:**

1. Run `/upgrade` to refresh `code-style.md` (table now lists `/preflight`).
2. Copy the `preflight.md` heredoc body from `bootstrap.sh` into
   `.claude/commands/preflight.md`, OR re-bootstrap a fresh project and copy the
   generated file.
3. Optional: add a "Run `/preflight` first; abort on FAIL" reminder at the top of
   your project's `deploy.md` and `release.md` command files.

**For `verify-review`** (one-time global install):

```bash
mkdir -p ~/.claude/skills/verify-review
cp _playbook/reference/verify-review-SKILL.md ~/.claude/skills/verify-review/SKILL.md
# (or write the file manually using the content from the skill file)
```

The skill activates automatically when you paste a review report, reference a PR review
URL, or ask Claude to "address" / "fix" / "act on" / "triage" findings from an external
tool.

**Why this matters:** Insights data showed (a) three deploy sessions blocked by ASC
char-limit violations or missing `promotional_text` fields, and (b) at least two
sessions where Claude rubber-stamped Codex false-positives until the user pushed back.
Both are mechanical to prevent with the right scaffolding.

---

## 2026-04-27 — Track B replaced: appshot-cli + Apple Frames CLI (no more AppMockUp)

> **Superseded by:** 2026-05-03 — appshot retirement + watch composition cleanup (Phase 6 finished). Track B is now shotsmith; do **not** install appshot-cli or run `patch-appshot.sh` from this entry — that scaffolding has been removed.

**What changed:** §Phase 5 Track B (marketing screenshots with captions and
gradient backgrounds) now recommends a CLI pipeline — `appshot-cli` layered on
top of Apple Frames CLI — instead of AppMockUp Studio. Web-based mockup tools
(AppMockUp, AppDrift, AppLaunchpad) are removed entirely. The new pipeline is
scriptable, agent-friendly, reproducible, and produces designs that are easier
to tune across releases.

**Pipeline:**

```
raw simctl/UITest PNGs
        ↓ frames CLI (Track A)
framed PNGs
        ↓ appshot build --no-frame
final marketing PNGs
        ↓ deliver
App Store Connect
```

**Bootstrap-emitted artifacts (new):**

- `fastlane/appshot/.appshot/config.json` — starter with sunset gradient
  (`#FF5F6D → #FFC371`) and "New York Small Bold" caption font. Tune per
  project.
- `fastlane/appshot/.appshot/captions/{iphone,ipad}.json` — caption skeletons
  with placeholders for two screenshots; format is
  `{filename: {lang: caption}}`.
- `fastlane/appshot/screenshots/{iphone,ipad}/` — staged input dirs (gitignored).
- `fastlane/appshot/final/` — appshot output dir (gitignored).
- `scripts/patch-appshot.sh` — idempotent patch that bumps appshot v2's
  caption font caps. Tunable via `APPSHOT_IPHONE_FONT` / `APPSHOT_IPAD_FONT`
  env vars (defaults: 115 / 130). **Re-run after every `npm install -g
  appshot-cli`** — patches live inside `node_modules/`.
- `appshot_screenshots` lane in the bootstrap Fastfile. Stages framed PNGs
  per locale, runs `appshot build --langs <lang>`, copies captioned output
  back to the deliver dirs. Defaults: `locale:en-US lang:en`. Multi-locale
  projects call once per locale (`bundle exec fastlane appshot_screenshots
  locale:es-ES lang:es`).
- `frame_screenshots` lane updated to **automatically preserve raws** in
  `fastlane/screenshots/{locale}/<device>/raw/` on first run. Re-framing
  with a different bezel color or re-captioning with new copy no longer
  requires re-capturing on the simulator. Lesson learned from Flara, where
  the `raw/` discipline was added too late.
- `.gitignore` updated for appshot intermediates.

**Caption font naming gotcha (documented):** appshot's `parseFontName` only
recognizes the literal suffixes `Bold` and `Italic`. To get the bold weight of
a macOS optical-size variant (e.g. New York Small, New York Medium), the font
name must literally end in `Bold`. Apple's font license permits SF Pro and
the New York family for marketing materials about Apple-platform apps.

**One-time install (manual, per machine):**

```bash
npm install -g appshot-cli
./scripts/patch-appshot.sh
```

**Recommended Workflow table** updated to reflect the new flow with a
separate "Caption / Background" column.

**To adopt in existing projects:**
1. Run the install commands above.
2. Copy `fastlane/appshot/`, `scripts/patch-appshot.sh`, the `.gitignore`
   additions, and the `appshot_screenshots` lane (plus the `raw/`
   preservation block in `frame_screenshots`) from a freshly-bootstrapped
   project — or run `/upgrade` if you have it wired up.
3. Edit `.appshot/config.json` and `.appshot/captions/{iphone,ipad}.json`
   for your project's gradient, font, and copy.
4. Capture + frame: `bundle exec fastlane screenshots`.
5. Caption: `bundle exec fastlane appshot_screenshots` (per locale).
6. Upload: `bundle exec fastlane upload_screenshots`.

**Why no more AppMockUp:** the web UI is janky, breaks reproducibility (manual
clicks per run), and isn't agent-driveable. Hand-tuned CLI config that lives
in the repo is faster to iterate and survives across releases.

---

## 2026-04-26 — Screenshot pipeline hardening (status bar, snapshot races, uninstall warning)

> **Partially superseded by:** 2026-05-03 — Agent-driven manual-capture pipeline + Control Center retirement. The status-bar fix is now codified in `.claude/rules/status-bar-overrides.md`; the widget/Control Center heredoc fixes are moot because those scripts are no longer emitted (replaced by the agent-driven `/capture-manual-surfaces` flow). Only un-migrated projects still acting on this entry need the heredoc edits — fresh bootstraps don't.

Five lessons curated out of the playbook inbox after the Flara v2.0 screenshot
session. All five fix real bugs or prevent ~10–15 minute foot-guns.

**What changed:**

1. **`bootstrap.sh` status-bar overrides** — `capture_widgets.sh` and
   `capture_control_center.sh` heredocs now include `--dataNetwork hide` and
   `--operatorName ""`. Without these flags, the 5G/LTE label takes width next
   to the cellular bars and pushes the Wi-Fi icon onto a second row inside
   Control Center. Affects every project bootstrapped before today.
2. **Playbook §Phase 5 — "Reference: cleanest manual status-bar override"**
   subsection added (after Step 1) with the full `simctl status_bar` command and
   a caveat that `--time` only sets the *visible status-bar time/date display*,
   not the iOS system clock (so Calendar widgets / Lock Screen big date /
   Notification Center always show today's actual date — there is no public
   `simctl date` and no simulator-only workaround as of iOS 26).
3. **Playbook §Phase 5 — "XCUITest tips that save reshoots"** subsection added.
   Two patterns: (a) prefer direct accessibility-identifier taps over
   `press(forDuration:)` + contextMenu items in screenshot tests — direct taps
   are dramatically more reliable; (b) any service that reads `UserDefaults` in
   `init()` (theme manager, settings singleton) must also synchronously check
   `-FASTLANE_SNAPSHOT` there — SwiftUI evaluates the first body using
   whatever `init()` produced *before* `.task` runs, so XCUITest can capture
   a frame using the persisted user value (e.g., dark mode) even when `.task`
   later corrects it. Includes a 10-line code example.
4. **Playbook §Phase 5 §2.5 + §2.6 — `simctl uninstall` warning** added. Never
   `xcrun simctl uninstall <DEVICE> <BUNDLE_ID>` in a capture pipeline.
   Uninstall removes the app **and all of its extensions/widgets** — wiping
   the user's manual placements of home-screen widgets, Lock Screen Live
   Activity widget, and Control Center widget. Reinstall does not bring those
   layouts back.

**To adopt in existing projects:**
- If your project's `fastlane/capture_widgets.sh` or
  `fastlane/capture_control_center.sh` predates 2026-04-26, replace the
  `xcrun simctl status_bar … override …` line with the new flag set (see
  playbook §Phase 5 reference command).
- If your project has a custom theme manager or settings singleton that reads
  `UserDefaults` in `init()`, add the `-FASTLANE_SNAPSHOT` synchronous check
  to prevent the dark/light race in screenshot tests.

---

## 2026-04-25 — Control Center capture lane (Control Widget apps)

> **Superseded by:** 2026-05-03 — Agent-driven manual-capture pipeline + Control Center retirement. The `control_center_screenshot` lane and `fastlane/capture_control_center.sh` helper are no longer emitted by bootstrap. Use `/capture-manual-surfaces` instead — the user performs the swipe, Claude Code captures the screenshot. Do **not** wire up the Quartz drag from this entry on new projects.

**What changed:** Added a `control_center_screenshot` Fastlane lane and a
`fastlane/capture_control_center.sh` helper for apps that ship a Control
Widget (ControlKit, iOS 18+). Control Center has no Simulator keyboard
shortcut, so the lane drives a synthesized mouse swipe via Python's
`Quartz CGEventPost` (PyObjC ships with Xcode Command Line Tools — no
extra dep).

**How it works:**
1. Boots the target simulator, overrides the status bar (9:41 / full signal).
2. Reads Simulator.app's window position via AppleScript.
3. Runs an inline Python script that posts a 25-step left-mouse drag from
   the top-right corner of the simulated screen down ~600pt, simulating
   the user pulling Control Center down.
4. Captures via `xcrun simctl io ... screenshot` once CC has settled.
5. Dismisses with Cmd+Shift+H and chains `frame_screenshots` unless
   `frame:false` is passed.

**One-time prerequisite — Accessibility permission:** synthesized mouse
events to another app require Accessibility permission. macOS prompts the
first time you run the lane (or silently refuses and Control Center stays
closed). Grant your terminal app access in **System Settings → Privacy &
Security → Accessibility**.

**When to use this:** only if your app ships a Control Widget. Without one,
Control Center shows just iOS defaults — no app-specific marketing value.
Skip the lane on apps that don't have a `ControlWidget` target.

**Affected files:** `bootstrap.sh` (new `capture_control_center.sh` HEREDOC
+ new `control_center_screenshot` lane in Fastfile), `ios-project-playbook.md`
§Phase 5 (new Step 2.6 with prerequisite walk-through and a troubleshooting
table), `.claude/rules/build-deploy.md` (lane added to the quick reference).

**Action needed in your project (Control Widget apps only):**
1. Re-run `bootstrap.sh` against the project, or copy
   `fastlane/capture_control_center.sh` over and paste the new lane into
   the Fastfile.
2. Grant Accessibility permission to your terminal app (one-time per machine).
3. Run `bundle exec fastlane control_center_screenshot` to verify the swipe
   actually opens Control Center. If it doesn't, recheck the Accessibility
   permission — the script reports successfully but the gesture is suppressed
   without it.

---

## 2026-04-25 — Lock-screen + home-screen widget capture lane

**What changed:** Added a `widget_screenshots` Fastlane lane and a companion
`fastlane/capture_widgets.sh` helper to the bootstrap. The lane drives `xcrun
simctl` plus a small AppleScript to do what Fastlane `snapshot` can't: capture
the simulator's lock screen (with a Live Activity) and home screen (with a
widget) for App Store screenshots.

**How it works:**
1. Boots the target simulator (default: iPhone 17 Pro Max), overrides the
   status bar to 9:41 / full signal / charged.
2. Launches the app with `-WIDGET_DEMO_MODE YES -FASTLANE_SNAPSHOT YES` so the
   app can auto-start a deterministic Live Activity for capture (you wire the
   launch-arg check into your `@main` App).
3. Sends Cmd+L via AppleScript to lock the simulator, captures the lock screen
   with the Live Activity visible.
4. Goes home (Cmd+Shift+H), captures the home screen with the widget.
5. Optionally chains `frame_screenshots` to apply Apple Frames.

**One-time manual prep per simulator:** drop the widget on the home screen via
the simulator UI once — the placement persists in the simulator's
`CoreSimulator` data container across boots, so subsequent automated runs find
the widget already in place.

**Known limitations** (documented inline in §Phase 5):
- Dynamic Island is a compositor overlay and doesn't appear in `simctl
  screenshot` output — capture those on a real device.
- StandBy mode requires a real device charging in landscape; no simulator path
  on iOS 26.
- Simulator must hold focus during the AppleScript `keystroke` calls (don't
  run on a machine where you're actively typing).

**Affected files:** `bootstrap.sh` (new `capture_widgets.sh` HEREDOC + new
`widget_screenshots` lane in Fastfile), `ios-project-playbook.md` §Phase 5
(new Step 2.5 section), `.claude/rules/build-deploy.md` (lane added to the
quick reference list).

**Action needed in your project:**
1. Re-run `bootstrap.sh` against the project, or copy `fastlane/capture_widgets.sh`
   from the playbook and add the `widget_screenshots` lane to your Fastfile.
2. Add the `-WIDGET_DEMO_MODE` launch-arg branch in your `@main` App that
   starts a canned `ActivityKit` activity.
3. Manually place the widget on the home screen of each capture simulator
   (one-time per device).
4. Run `bundle exec fastlane widget_screenshots` to verify; outputs land at
   `fastlane/screenshots/en-US/iPhone 6.9" Display/9{0,1}_*.png`.

---

## 2026-04-25 — Doc fixes: `.env.project` flow + XcodeBuildMCP install command

**What changed:** Two stale doc paths fixed after a Codex review pass.

1. **`.env.project` flow** — `README.md` (TL;DR + Setup) and `ios-project-playbook.md`
   §0.2 still told users to "edit `bootstrap.sh`" with `APP_NAME`, `BUNDLE_ID`, etc.
   That path was deprecated when the script switched to reading `.env.playbook` +
   `.env.project`. Both docs now point users at the env-file flow that
   `getting-started.md` already documented correctly. README also gained a
   `.env.project.example` row in the Files table.

2. **XcodeBuildMCP install command** — `claude-code-plugins-setup.md` was missing
   the trailing `mcp` subcommand on both `claude mcp add` snippets (lines 81 and
   94). Current `xcodebuildmcp` is a multi-command CLI (`mcp`, `init`, `setup`,
   `tools`, `simulator`, …) — without the `mcp` subcommand, the binary just
   prints help and exits, so the MCP server never starts. `getting-started.md`
   was already correct; both files are now in sync.

**Affected files:** `README.md`, `ios-project-playbook.md` §0.2,
`claude-code-plugins-setup.md`.

**Action needed in your machine setup:**
- If you ran the bare `claude mcp add ... xcodebuildmcp@latest` command from an
  older copy of `claude-code-plugins-setup.md` and XcodeBuildMCP isn't actually
  showing up in `/mcp` inside Claude Code, re-run with the trailing `mcp`:
  ```bash
  claude mcp remove XcodeBuildMCP
  claude mcp add --transport stdio XcodeBuildMCP -- npx -y xcodebuildmcp@latest mcp
  ```
- No project-level changes — these are doc + per-machine MCP config fixes only.

---

## 2026-04-24 — Screenshot simulators updated to ASC's two accepted sizes

**What changed:** Phase 5 and `bootstrap.sh` Snapfile now capture on only the two
simulators whose output pixel dimensions ASC actually accepts as submissions:

- **iPhone 17 Pro Max** (1320×2868, 6.9") — replaces iPhone 14 Plus
- **iPad Pro 13-inch (M5)** (2064×2752) — unchanged

Per [Apple's current screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/),
6.9" is the primary required iPhone size (6.5" is a fallback when 6.9" is absent),
and ASC auto-scales the 6.9" submission down to 6.5", 6.3", 6.1", and older sizes.
Same scaling applies from iPad 13" → 11". Uploading only 6.3" iPhone or 11" iPad
screenshots blocks "Add for Review."

**Why this matters:**
- One simulator run (two devices) replaces the previous three-device capture.
- Apple Frames CLI has a native iPhone 17 Pro Max frame — auto-detection is exact,
  no fallback to an older bezel.
- Aligns with 2026 indie-dev consensus (Screenhance, FrameHero, SplitMetrics,
  MobileAction guides all recommend capturing at the largest accepted size and
  leaning on ASC auto-scale).

**AppMockUp escape hatch:** If you want iPhone 17 Pro or iPad Pro 11" as your
*visible* marketing frame (because those are your users' most common devices),
route through Track B — AppMockUp composites at ASC canonical resolutions
regardless of source capture size, so you can show any device while still meeting
ASC's pixel-dimension requirement.

**Affected files:** `ios-project-playbook.md` §Phase 5 (Required Device Sizes
table, important note, Snapfile sample, Apple Frames CLI device-detection note),
`bootstrap.sh` (Snapfile HEREDOC), `.claude/rules/build-deploy.md` (simulator
table).

**Action needed in your project:**
1. Update `fastlane/Snapfile` — replace `iPhone 14 Plus` with `iPhone 17 Pro Max`.
2. Delete any existing 6.5"-only screenshots in `fastlane/screenshots/en-US/iPhone 6.5" Display/`
   after the next capture run (or let `clear_previous_screenshots(true)` handle it).
3. If you had manually uploaded 6.3" or 11" screenshots to ASC, replace them with
   the 6.9" / 13" sets on your next submission.

---

## 2026-04-23 — Chain frame_screenshots into screenshots lane

**What changed:** The bootstrapped `screenshots` Fastfile lane now calls
`frame_screenshots` at the end, so `bundle exec fastlane screenshots` captures AND
frames in one command. Running framing standalone against pre-captured screenshots is
still supported via `bundle exec fastlane frame_screenshots`.

**Affected files:** `bootstrap.sh`, `ios-project-playbook.md` §Phase 5,
`.claude/rules/build-deploy.md`

**Action needed in your project:** If your Fastfile was bootstrapped with the earlier
separate lanes, update the `screenshots` lane to call `frame_screenshots` after
`capture_screenshots`. See `bootstrap.sh:344-350`.

---

## 2026-04-23 — Apple Frames CLI is the default framing tool

**What changed:** Phase 5 Screenshot Workflow in `ios-project-playbook.md` now recommends
Federico Viticci's [Apple Frames CLI](https://github.com/viticci/frames-cli) as the
default framing step, replacing AppMockUp Studio as the first-choice tool. AppMockUp
stays as "Track B" for marketing designs that need captions and branded backgrounds.

- **New Track A (default) in Step 2** — install + setup instructions, Fastlane-friendly
  one-liner, device-detection note (1284×2778 auto-frames as iPhone 13 Pro Max; no
  iPhone 14 bezel exists in the library).
- **New Fastfile lane `frame_screenshots`** in `bootstrap.sh` — runs `frames` on each
  device subfolder under `fastlane/screenshots/en-US/`.
- **Updated "Recommended Workflow by Project Stage" table** — Apple Frames CLI across
  all stages; AppMockUp reserved for marketing-heavy apps.
- **Removed `frameit` mention** — superseded by Apple Frames CLI.
- **Optional Claude Code skill** — the CLI ships a skill at `skill/SKILL.md`; install
  once to `~/.claude/skills/frames-cli/SKILL.md` for agent-native flag awareness.

**Affected files:** `ios-project-playbook.md`, `bootstrap.sh`,
`.claude/rules/build-deploy.md`

**Action needed in your project:**
1. Install the CLI: `git clone https://github.com/viticci/frames-cli.git && cd frames-cli && pip3 install Pillow && ln -s "$(pwd)/frames" ~/.local/bin/frames && frames setup`
2. (Optional) Install the Claude Code skill from `frames-cli/skill/SKILL.md` to `~/.claude/skills/frames-cli/`
3. If your Fastfile was bootstrapped before today, add the `frame_screenshots` lane (see `bootstrap.sh:350-355`) and call it between `fastlane snapshot` and `fastlane upload_screenshots`

---

## 2026-04-21 — CloudKit sync patterns added to §4.4

**What changed:** Three lessons from the Flara project added to §4.4 CloudKit & Push
Notifications in `ios-project-playbook.md`:

- **CKQuery + encrypted fields pitfall** — new row in Common CloudKit Pitfalls table:
  never use `CKQuery` on encrypted-only record types in Production; use
  `recordZoneChanges(since: nil)` instead.
- **Debounce push pattern** — cancel-and-debounce concurrent `save()` calls to prevent
  last-writer-wins race conditions under `savePolicy: .changedKeys`.
- **Three sync triggers** — always implement silent push + 15s polling + pull-to-refresh;
  `CKDatabaseSubscription` alone is unreliable on TestFlight/low battery.

**Affected files:** `ios-project-playbook.md`
**Action needed in your project:** Review your CloudKit sync layer against these patterns.

---

## 2026-04-10 — Externalize config to env files, fix bootstrap path resolution

**What changed:** `bootstrap.sh` no longer requires manual editing. All configuration is
loaded from two gitignored env files:

- **`.env.playbook`** — identity and credentials (Team ID, GitHub org, ASC keys). Set once.
- **`.env.project`** — app-specific vars (APP_NAME, BUNDLE_ID, REPO_NAME, MINIMUM_IOS).
  Edit before each bootstrap run.

**Bug fixes:**
- Fixed two `BASH_SOURCE[0]` relative path resolution bugs that caused bootstrap to fail
  after `cd`-ing into the new project directory (lines 905 and 943). Both now use
  `SCRIPT_DIR` resolved once at script start.

**New files:**
- **`.env.project.example`** — template for per-project config

**Updated files:**
- **`bootstrap.sh`** — sources env files, validates required vars, removed hardcoded placeholders
- **`.gitignore`** — added `.env.project`
- **`getting-started.md`** — updated one-time setup (add `.env.playbook` step) and
  per-project workflow (use `.env.project` instead of editing script). Steps renumbered
  from 5 to 4.

**How to upgrade your project:** No project-side changes needed — this only affects the
playbook's bootstrap workflow. Existing projects are unaffected.

---

## 2026-04-09 — Session lifecycle commands, /upgrade, testing + privacy rules

**What changed:** Major expansion of slash commands and rules:

**New slash commands:**
- **`/status`** — automated session startup briefing (replaces the startup checklist rule).
  Shows project state, branch, last session summary, flags for uncommitted changes,
  pending manual tasks, stale rules, and open Dependabot PRs.
- **`/wrapup`** — automated session end (replaces the end checklist rule). Commits,
  updates CLAUDE.md Current State, writes WORKLOG entry, updates release notes, pushes.
- **`/upgrade`** — syncs a project with playbook changes. Reads CHANGELOG.md, identifies
  entries newer than the project's `.playbook-version` marker, walks through each change
  with apply/skip/manual recommendations.
- **`/context-health`** — session hygiene gauge. Reports uncommitted files/lines, push
  status, WORKLOG freshness. Recommends checkpoint when indicators are high.

**New rules:**
- **`testing.md`** — testing strategy for solo indie v1 (what to test, what to skip,
  Swift Testing conventions, no-mock persistence philosophy)
- **`privacy-manifest.md`** — when and how to update PrivacyInfo.xcprivacy, required
  reason API categories, third-party SDK guidance

**Removed:**
- **`session-checklists.md`** — replaced by `/status` and `/wrapup` commands

**Other changes:**
- `bootstrap.sh` now copies all playbook slash commands (except `/curate`) into projects
- `bootstrap.sh` creates `.playbook-version` file for `/upgrade` tracking
- Slash commands table in `code-style.md` updated with all 10 commands

**Playbook files affected:** `.claude/commands/` (4 new), `.claude/rules/` (2 new, 1 removed),
`bootstrap.sh`, `.claude/rules/code-style.md`

**How to upgrade your project:**

1. Delete `.claude/rules/session-checklists.md` (replaced by commands)
2. Copy new rules from playbook `.claude/rules/`: `testing.md`, `privacy-manifest.md`
3. Copy new commands from playbook `.claude/commands/`: `status.md`, `wrapup.md`,
   `upgrade.md`, `context-health.md`
4. Create `.playbook-version` in project root with today's date:
   ```
   # Last synced with playbook CHANGELOG
   2026-04-09
   ```
5. Update the slash commands table in `.claude/rules/code-style.md` (add `/status`,
   `/wrapup`, `/upgrade`, `/context-health`)

---

## 2026-04-09 — Add cross-project playbook inbox with slash commands

**What changed:** New `inbox.md` file in the playbook root serves as a shared inbox where
Claude Code sessions in any bootstrapped project can log lessons learned, gotchas,
suggestions, and patterns. Two slash commands drive the workflow:

- **`/inbox {lesson}`** — available in every bootstrapped project. Logs a structured
  entry (date, project, category, context, lesson, suggested action) to the playbook's
  `inbox.md`. Can be run with an argument or interactively.
- **`/curate`** — available in the `_playbook/` directory. Walks through inbox entries
  one by one, recommends adopt/defer/discard, makes adopted changes to playbook files,
  and cleans up processed entries.

A `.claude/rules/playbook-inbox.md` rule provides guidance on what qualifies as inbox-worthy.
`bootstrap.sh` substitutes the absolute playbook path into the rule and copies the `/inbox`
command at project creation time.

**Playbook files affected:** `inbox.md` (new), `.claude/rules/playbook-inbox.md` (new),
`.claude/commands/inbox.md` (new), `.claude/commands/curate.md` (new), `bootstrap.sh`,
`.claude/rules/code-style.md` (slash commands table)

**How to upgrade your project:**

1. Copy `.claude/rules/playbook-inbox.md` from the playbook into your project's
   `.claude/rules/`
2. Replace `PLAYBOOK_PATH` in the copied file with the absolute path to your
   `_playbook/` directory (e.g. `~/Code/_playbook`)
3. Copy `.claude/commands/inbox.md` from the playbook into your project's
   `.claude/commands/`

---

## 2026-04-09 — Restructure CLAUDE-TEMPLATE.md: extract rules to .claude/rules/

**What changed:** CLAUDE-TEMPLATE.md reduced from 542 lines to ~190 lines. All operational
rules (git workflow, build/deploy, code style, WWDC25, session checklists, manual tasks,
work log) extracted into path-scoped `.claude/rules/` files that Claude Code loads
automatically by glob match. Two new rules added:

- **session-health.md** — context window awareness, proactive checkpointing, crash recovery
- **git-workflow.md** — now includes git timing guidance (commit early and often)

The core CLAUDE-TEMPLATE.md retains only project identity: overview, tech stack, UI
direction, data models, monetization, scope rules, key decisions, and App Store metadata.

`bootstrap.sh` updated to copy `.claude/rules/` files into bootstrapped projects.

**Playbook files affected:** `CLAUDE-TEMPLATE.md`, `bootstrap.sh`, `.claude/rules/` (new)

**How to upgrade your project:**

1. Create `.claude/rules/` directory in your project root
2. Copy all `.md` files from the playbook's `.claude/rules/` into your project's
   `.claude/rules/`
3. Remove the following sections from your project's `CLAUDE.md` (they now live in rules):
   - Code Style & Conventions
   - Automated Quality Tools
   - WWDC25 & iOS 26 Awareness
   - Git & Version History
   - Build & Deploy
   - Session Startup Checklist / Session End Checklist
   - Manual Tasks Handoff Rule
   - Work Log Rule
4. Add a note near the top of your `CLAUDE.md` pointing to `.claude/rules/`:
   > Operational rules (git workflow, build/deploy, code style, WWDC25, session checklists,
   > manual tasks, work log, session health) live in `.claude/rules/` and are loaded
   > automatically by path glob. Do not duplicate them here.

---

## 2026-04-09 — Public release: PII scrub + .env.playbook pattern

**What changed:** Scrubbed all personal identifiers, Apple Developer credentials,
and hardcoded org/domain references to prepare the playbook for public GitHub release.

- All Team IDs, ASC Key IDs, Issuer IDs, email, name, and domain replaced with
  generic placeholders (`YOUR_TEAM_ID`, `com.example.*`, etc.)
- Added `.env.playbook.example` — users copy to `.env.playbook` and fill in their
  own values. `.env.playbook` is gitignored.
- `bootstrap.sh` config section now has a comment pointing to `.env.playbook`
- File paths using absolute `/Users/...` replaced with `~` shorthand
- Example project names generalized to `MyApp`

**Playbook files affected:** All files.

**How to upgrade your project:**

1. Copy `.env.playbook.example` to `.env.playbook` and fill in your Apple Developer
   credentials (Team ID, ASC Key ID, Issuer ID, org, email, domain)
2. Add `.env.playbook` to your global gitignore if not already covered

---

## 2026-04-08 — CloudKit & Push Notifications gotchas + async init pattern

**What changed:** Added §4.4 covering CloudKit + Push Notifications integration
gotchas learned across multiple projects. Also added async init and
debugging tips to §3.3 Code Style.

New coverage:
- **CloudKit pitfalls table** — "Invalid bundle ID" fix, Simulator flakiness,
  Production schema immutability, CKError.unknownItem on empty containers
- **aps-environment rule** — use `development` in source; Xcode handles production
- **Self-healing async init pattern** — mutation paths re-verify preconditions,
  with Swift code example for CloudKit push
- **print() debugging tip** — when Logger categories don't surface in Xcode console

**Playbook files affected:** `ios-project-playbook.md`

**How to upgrade your project:**

These are reference sections — no project file changes needed. If your project
uses CloudKit, review §4.4 for gotchas. The async init pattern (§4.4) and
debugging tip (§3.3) apply to any project.

---

## 2026-04-02 — Automated release lane with metadata and screenshots

**What changed:** The release pipeline is now fully automated. Previously the `release`
lane skipped both metadata and screenshots (`skip_metadata: true`). Now it syncs metadata
from `fastlane/metadata/en-US/` to App Store Connect on every release.

New additions:
- **Pre-populated metadata files** — `name.txt`, `description.txt`, `release_notes.txt`,
  URLs auto-filled with GitHub Pages links; new `promotional_text.txt` and `marketing_url.txt`
- **Deliverfile** — configures `deliver` with safe defaults (`force: true`, no auto-submit)
- **Snapfile** — configured for required ASC device sizes (6.5" iPhone, iPad 13")
- **ScreenshotTests.swift** — UI test template for automated screenshot capture
- **Commented-out UI test target** in `project.yml` (uncomment after `fastlane snapshot init`)
- **3 new Fastlane lanes:** `screenshots`, `upload_metadata`, `upload_screenshots`
- **release.yml** — GitHub Actions workflow for App Store release (manual dispatch)
- **`/release` slash command** — validates metadata, syncs, builds, uploads, tags

**Playbook files affected:** `bootstrap.sh`, `CLAUDE-TEMPLATE.md`

**How to upgrade your project:**

1. Create `fastlane/Deliverfile`:
   ```ruby
   app_identifier CredentialsManager::AppfileConfig.try_fetch_value(:app_identifier)
   force true
   submit_for_review false
   automatic_release false
   precheck_include_in_app_purchases false
   ```

2. Create `fastlane/Snapfile` (update scheme and devices for your app):
   ```ruby
   # Devices matching ASC required screenshot sizes
   devices([
     "iPhone 14 Plus",             # 6.5" — REQUIRED for submission (1284x2778)
     "iPad Pro 13-inch (M5)"      # 13"  — REQUIRED for submission (2064x2752)
   ])
   languages(["en-US"])
   scheme("YourAppUITests")
   output_directory("./fastlane/screenshots")
   clear_previous_screenshots(true)
   override_status_bar(true)
   ```
   **Important:** ASC requires iPhone 6.5" screenshots (1284x2778). iPhone 17 Pro
   outputs 6.3" resolution — it does NOT satisfy this requirement. Use iPhone 13 Pro Max
   or iPhone 14 Plus for the mandatory 6.5" size.

3. Populate `fastlane/metadata/en-US/` files with real content (name, description,
   keywords, release notes, URLs). Add `promotional_text.txt` and `marketing_url.txt`.

4. Add 3 new lanes to your `Fastfile` (`screenshots`, `upload_metadata`,
   `upload_screenshots`) — see `bootstrap.sh` for the full lane definitions.

5. Update the `release` lane: change `skip_metadata: false`, add `force: true`.

6. Copy `.github/workflows/release.yml` from `bootstrap.sh` (mirrors `testflight.yml`
   but runs `fastlane release`).

7. Copy `.claude/commands/release.md` from `bootstrap.sh`.

8. Add `/release` row to your `CLAUDE.md` slash commands table.

9. Create `fastlane/screenshots/en-US/` directory and `fastlane/screenshots/.gitkeep`.

10. (Optional) Create `YourAppUITests/ScreenshotTests.swift` and uncomment the UI test
    target in `project.yml` after running `bundle exec fastlane snapshot init`.

---

## 2026-04-02 — Harden /deploy command (profile check, PATH fix, cleanup)

**What changed:** The `/deploy` slash command now checks that provisioning profiles are
installed locally *before* running fastlane. Previously, fastlane would modify
`project.pbxproj` with signing settings, then fail when profiles were missing — leaving
dirty project files that had to be manually restored.

Also fixed: SwiftLint now uses full Homebrew path (`/opt/homebrew/bin/swiftlint`), the
fastlane invocation includes PATH and locale exports in both template versions, and the
fallback section now includes `git checkout -- *.xcodeproj` to restore project files.

**Playbook files affected:** `bootstrap.sh`, `ios-project-playbook.md` (deploy command)

**How to upgrade your project:**

Replace `.claude/commands/deploy.md` with the updated version. Key changes:
1. New step 1 checks `~/Library/MobileDevice/Provisioning Profiles/` for required
   profiles before running fastlane — stops early if missing
2. SwiftLint uses full path: `/opt/homebrew/bin/swiftlint lint --strict --quiet`
3. Fastlane invocation includes PATH + locale exports:
   `export PATH="/opt/homebrew/opt/ruby/bin:$PATH" && export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && set -a && source .env.fastlane && set +a && bundle exec fastlane beta`
4. Fallback now restores project files: `git checkout -- *.xcodeproj`

See `bootstrap.sh` or `ios-project-playbook.md` for the full updated command.

---

## 2026-04-02 — Fix lefthook pre-commit hooks (PATH + glob)

**What changed:** Two fixes to `lefthook.yml`:

1. **PATH fix:** Claude Code sessions don't always inherit the full shell PATH, so
   Homebrew-installed binaries (`gitleaks`, `swiftlint`) fail with `command not found`.
   Fixed by using full paths (`/opt/homebrew/bin/...`).

2. **Glob fix:** Lefthook's default glob matcher (`gobwas`) treats `**` as matching 1+
   directories, not 0+. So `*.{swift}` only matched root-level files and missed
   subdirectories. Fixed by adding `glob_matcher: doublestar` (standard behavior where
   `**` matches 0+ directories) and using `**/*.{swift}` as the glob pattern.

**Playbook files affected:** `bootstrap.sh`, `ios-project-playbook.md` (lefthook template
+ troubleshooting table)

**How to upgrade your project:**

Replace your `lefthook.yml` with:

```yaml
glob_matcher: doublestar

pre-commit:
  parallel: true
  commands:
    swiftlint:
      glob: "**/*.{swift}"
      run: /opt/homebrew/bin/swiftlint lint --strict --quiet {staged_files}
    gitleaks:
      run: /opt/homebrew/bin/gitleaks protect --staged --verbose

commit-msg:
  commands:
    conventional-commit:
      run: |
        MSG=$(head -1 "{1}")
        echo "$MSG" | grep -qE '^(feat|fix|docs|refactor|test|chore|ui|perf|ci)(\([a-z0-9-]+\))?!?: .{1,72}$' || \
        (echo "❌ Commit message must follow conventional commits format" && \
         echo "   Example: feat(live-activity): add stop button" && exit 1)
```

The `commit-msg` hook uses only shell builtins (`head`, `grep`, `echo`) so it doesn't
need the PATH fix.

---

## 2026-04-02 — Document multi-target fastlane signing for app extensions

**What changed:** Added comprehensive guidance for signing app extensions (widgets, share
extensions, etc.) in fastlane and CI. The bootstrap Fastfile template now includes
comments showing where to add extension targets. Section 4.1 in the playbook now covers
the full multi-target setup: Fastfile changes, CI provisioning profile installation,
GitHub secrets, and Apple Developer Portal checklist.

**Playbook files affected:** `ios-project-playbook.md` (§4.1 expanded),
`CLAUDE-TEMPLATE.md` (callout added to Build & Deploy), `bootstrap.sh` (Fastfile comments)

**How to upgrade your project:**

If your app has extension targets (widgets, etc.):
1. Update your `Fastfile` to add a `targets:` filter to the existing
   `update_code_signing_settings` call for the main app target
2. Add a second `update_code_signing_settings` block for each extension target with
   its own `profile_name`, `bundle_identifier`, and `targets` filter
3. Update `export_options.provisioningProfiles` in `build_app` to include all bundle IDs
4. Apply the same changes to both `beta` and `release` lanes
5. In `testflight.yml`, update the "Install provisioning profile" step to install
   each extension's profile as a separate `.mobileprovision` file, and update cleanup
6. Add `PROVISIONING_PROFILE_<EXT>` GitHub secrets for each extension

If your app is single-target, no changes needed.

---

## 2026-04-02 — Add WORKLOG.md session diary pattern

**What changed:** Projects now use a separate `WORKLOG.md` file as a gitignored session
diary. CLAUDE.md remains the stable reference doc; WORKLOG.md tracks what happened
session by session (what changed, decisions, blockers). This keeps CLAUDE.md clean and
gives new sessions rich context without re-reading the codebase.

**Playbook files affected:** `CLAUDE-TEMPLATE.md`, `bootstrap.sh`,
`ios-project-playbook.md`, `getting-started.md`

**How to upgrade your project:**

1. Add `WORKLOG.md` to your `.gitignore` (alongside `MANUAL-TASKS.md`)
2. Create `WORKLOG.md` in your project root with this header:
   ```markdown
   # [APP_NAME] Work Log

   > Session diary for Claude Code sessions. Reverse-chronological.
   > CLAUDE.md is the reference doc; this file tracks what happened session by session.
   > This file is gitignored — local scratchpad only.

   ---
   ```
3. In your `CLAUDE.md`, update the "Current State" callout to:
   > Update this section and WORKLOG.md at the end of every session. CLAUDE.md gets a
   > summary update; WORKLOG.md gets the detailed session diary entry.
4. Add to your Session Startup Checklist (as step 2, after reading CLAUDE.md):
   - **Read `WORKLOG.md`** — review recent session history for context
5. Add to your Session End Checklist (after updating Current State):
   - **Update `WORKLOG.md`** with detailed session diary entry
6. Add the "Work Log Rule" section to your CLAUDE.md (see `CLAUDE-TEMPLATE.md` for
   the full section including entry format and rules)
7. If your CLAUDE.md has accumulated session history in the Current State section,
   migrate it into WORKLOG.md entries and trim Current State back to a summary
