# Commands architecture — universal + extensible, without the drift

> Design for making playbook commands/tools universal across projects yet extensible per
> project. Extends Stage 1a of `REFACTOR-PLAN.md`. Supersedes the *design* portion of
> `~/.claude/plans/hazy-dreaming-ocean.md` while keeping all of its verified gotchas and
> acceptance gates. **Status: proposed — refined after cross-review; pending sign-off before Phase A.**

## The problem

`/status` and `/wrapup` exist in four hand-diverged variants — playbook-repo, the downstream
iOS template, c3d-bridge-modeler, shotsmith — each a shared skeleton plus project-specific
bolt-ons that were edited directly into the copied file. They are the two most-run commands, so
the drift is maximally visible. `/context-health` already has two slightly different copies too.

## Root cause

Two *different kinds* of variation got welded into one forked prose file:

- **Kind variation** — true of every project of a type. "Python project → run pytest, check
  `CHANGELOG` unreleased section, sync version files." "iOS app → build status, Dependabot lens,
  prose-humanizer on release notes, `.playbook-version` vs CHANGELOG."
- **Instance variation** — true of exactly one project. shotsmith's specific version-file triple
  (`VERSION` / `pyproject.toml` / `shotsmith/__init__.py`); Flara's provisioning profiles; c3d's
  specific Civil-3D verification steps.

When both live in one copied file, every project must fork to change either — and they all
drift. The fix is to separate the two and bind them at runtime.

## The model: three tiers + an escape hatch, bound at runtime

| Tier | Lives in | Owner | Carries | Shared by |
|---|---|---|---|---|
| **1. Universal skeleton** | playbook command file (one source) | playbook | the invariant verb, platform-agnostic | every project |
| **2. Kind layer** | `packs/<kind>/command-profile.md` | playbook | everything common to a project *type* | all projects of that kind |
| **3. Instance facts** | `.claude/project.yml` (optional, committed) | project | declarative facts a command needs and can't detect | nobody — per project |
| **Escape hatch** | `.claude/command-profile.local.md` (optional) | project | prose judgment for true one-offs / kinds-of-one | nobody |

The word *profile* is deliberate: `get_project_profile` is already a planned MCP verb
(`REFACTOR-PLAN.md` §3). Tier 2 (`command-profile.md` — behavior) and Tier 3 (`project.yml` —
facts) are the behavior- and fact-halves of the project profile that verb will expose.

**Tier 1 — universal skeleton.** Platform-agnostic. `@{upstream}`, never hardcoded
`origin/main`. Guard every optional artifact read (`CLAUDE.md`, `WORKLOG.md`, `MANUAL-TASKS.md`)
with "if present." Say *nothing* about `[skip ci]` — it conflicts across iOS vs playbook, so it
belongs in the kind layer. The skeleton opens with a fixed runtime hook that loads the profile
*before* acting:

> At command start — before anything that mutates — read `.claude/command-profile.md`,
> `.claude/command-profile.local.md`, and `.claude/project.yml` if present. Merge the
> `## /<thisverb>` instructions from each into this command's plan, then execute the combined
> flow **in order**. A read-only verb (`/status`) may fold the profile sections in anywhere —
> nothing mutates. A mutating verb (`/wrapup`) must place each profile step at its correct point:
> orient → **decide branch route** (create/switch to a feature branch if on `main`, so the commit
> lands there) → **apply profile record mutations** (changelog, version-file sync, worklog,
> release notes, prose-humanizer) → **run profile validation gates** (tests, preflight) → stage
> selectively → commit → **push / PR routing** → confirm.
>
> **Invariant:** mutating profile steps whose output should be committed run *before* staging;
> validation gates run *after* all intended mutations and *before* the commit; the branch
> decision precedes the commit so work never lands on `main`.

Ordering is load-bearing for mutating verbs: a record mutation (changelog, version bump) appended
after the commit lands uncommitted; a validation gate appended after the commit can't block it; a
branch decision appended after the commit has already hit `main`. `/status`, mutating nothing, is
immune — which is why one hook serves both.

**Tier 2 — kind layer.** One `command-profile.md` per pack, with a `## /status`, `## /wrapup`,
`## /test`… section per verb — the single home for type-level command behavior, both checks
*and* mutating workflow (branch routing, commit scopes, release steps). **Every step is
conditional** — guarded by a declared fact (`if test_command is set`), a cheap existence check
(`if CHANGELOG.md exists`), or pack presence — so one profile fits a whole family without
overfitting its richest member. `packs/python/command-profile.md` serves both shotsmith (tests +
version sync + CHANGELOG) and devpulse (none of those): each step fires only when its condition
holds. Split a kind (`python-lib` vs `python-cli`) only when a second project proves an
unconditional split is needed. iOS's Dependabot/build/prose-humanizer behavior moves here from
the forked template.

**Tier 3 — instance facts.** A tiny, *committed* `.claude/project.yml` holding only the
declarative facts a command genuinely needs and can't cheaply detect. Introduced lazily — a
project gets one only when it has such a fact. It is also exactly the structured input Stage 3
MCP tools will read, so this tier is the seam to that future.

```yaml
# shotsmith/.claude/project.yml
kind: python                    # selects packs/python/command-profile.md (inferable from pyproject.toml)
test_command: pytest -q         # /wrapup pre-commit gate and a future /test
version_files:                  # kept in sync on a release bump
  - VERSION
  - pyproject.toml
  - shotsmith/__init__.py
```

**Escape hatch — instance prose.** For genuine judgment that isn't a datum and isn't shared:
the playbook repo's own CHANGELOG/`Superseded by:` logic; c3d's `.dyn` merge-hostility and
Civil-3D manual-task handoff. Same `## /<verb>` section format as `command-profile.md`. A
*kind-of-one* (c3d today — the only Dynamo project) lives here until a second instance appears, at
which point its shared parts are promoted to `packs/<kind>/command-profile.md`. You're never
blocked waiting for a pack to exist.

### Why runtime binding is the keystone

The command *reads* `command-profile.md` + `command-profile.local.md` + `project.yml` when it
runs. That single choice is what lets one mechanism serve both bridge types:

- **iOS (composed copies via pinned submodule):** `compose-claude.sh` copies the skeleton and
  the pack's `command-profile.md` into `.claude/`. Self-contained, byte-identical-verifiable.
- **non-iOS (live symlinks):** `.claude/commands/status.md` and `.claude/command-profile.md` are
  symlinks into this tree; they're always current, no compose step.

Either way the *runtime* behavior is identical, because the command just reads whatever is in
`.claude/`. Compile-time `sed` substitution (today's `__PRIMARY_SIM__` model) cannot do this — a
symlinked repo has nothing to substitute into. So markers stay only for the handful of scalars
iOS already bakes at compose time; everything structural moves to runtime read.

### How the three circles close

- *Data or prose?* — split by nature, not preference: facts are data (`project.yml`), judgment
  is prose (`command-profile.md` / `command-profile.local.md`).
- *Where does shared-but-not-universal live?* — the pack, definitively. The escape hatch means a
  kind-of-one is never stuck.
- *Do two bridge types need two mechanisms?* — no. Runtime binding is one mechanism for both.

## Coverage proof — the four variants map cleanly

| Old variant | Tier 1 (skeleton) | Tier 2 (kind) | Tier 3 / escape hatch |
|---|---|---|---|
| iOS template | branch, dirty, ahead/behind, recent commits, PRs, optional-artifact reads | `packs/ios/command-profile.md`: Dependabot, build status, `.playbook-version`→`/upgrade`, release-notes-draft, prose-humanizer, `[skip ci]` local/cloud, scope items | `.env.project` markers (sim, profiles, locales) |
| shotsmith | same | `packs/python/command-profile.md`: pytest gate, CHANGELOG-unreleased, `gh run list` CI | `project.yml`: `version_files`, `test_command` |
| c3d | same | (no second Dynamo project yet) | `command-profile.local.md`: Civil-3D `## Current Phase`, `.dyn` merge-hostility, manual-task handoff format, "does NOT check CI/Dependabot" |
| playbook repo | same | n/a (kind-of-one) | `command-profile.local.md`: CHANGELOG entry + `Superseded by:` tree, downstream-visible decision, inbox pending-count + `/curate`, stale-branch prune |

**Acceptance gate (from hazy-dreaming-ocean.md, step 4):** for each old variant, confirm
`(skeleton + its kind profile + its instance facts)` reproduces every step of the original.
Watch specifically for prose-humanizer, `[skip ci]`, release-notes (iOS); pytest pre-commit gate
+ version-file sync + CHANGELOG-unreleased (shotsmith); `.dyn` merge-hostility + Civil-3D
MANUAL-TASKS format (c3d).

## Generalization and the MCP seam

- **Other verbs.** The same skeleton-plus-hook applies to `/context-health`, `/preflight`,
  `/test`. Convert each on contact — when it next needs a touch — not in a big bang. A new verb
  is a new `## /<verb>` section in the kind `command-profile.md`, nothing more.
- **Stage 3 (MCP tools).** The dynamic verbs (`status`, `wrapup`, `context-health`, `conform`,
  `inbox`, `upgrade`) become MCP *tools*. They read the same `.claude/project.yml` this design
  already introduces, and can fold in the same `command-profile.md` prose. The universal logic
  moves into the server; the per-kind/instance data stays declared where it is. No
  re-architecture — the runtime-read contract is already tool-shaped. (Per the locked decision,
  MCP is the highest maintenance + security surface and comes only after the Claude prompt path
  works end-to-end.)

## Alternatives considered

- **Keep one `project-checks.md` per project (hazy-dreaming as-is).** Rejected as the endpoint:
  it mixes kind and instance, so same-kind projects re-derive and re-drift. This design is its
  refinement — same runtime-hook idea, split into kind/instance, and renamed (a profile carries
  mutating workflow, not just "checks").
- **Pure detection, no per-project files** (sniff `pyproject.toml` → Python, `*.xcodeproj` →
  iOS). Rejected as the *primary* mechanism: detection picks a *kind* well but can't express
  *instance judgment* (".dyn is merge-hostile"), and pushing kind logic into the universal file
  bloats the one file we most want stable. Kept as a *convenience*: `kind:` in `project.yml` is
  explicit but inferable, so detection can default it.
- **Make everything an MCP tool now.** Rejected per the locked sequencing — MCP is Phase 2/3,
  "only when earned." This design is the prompt-first path MCP later consumes.

## Rollout (sequenced; survives context loss)

Carries forward every gotcha from `~/.claude/plans/hazy-dreaming-ocean.md` — read it for the
verified specifics. Never push `main`; commit with explicit pathspecs (the dirty `inbox.md`
must stay unstaged).

**Phase 0 — lock the contract (this doc).** Tier names, file names (`command-profile.md`,
`command-profile.local.md`, `project.yml`), the `## /<verb>` section convention, and the
load-first runtime hook. No behavior change.

**Phase A — playbook source (one PR in `_playbook`, branch `feat/universal-status-wrapup`).**
1. Rewrite `.claude/commands/{status,wrapup}.md` to the universal skeleton + load-first hook.
2. Author `packs/ios/command-profile.md` and `packs/python/command-profile.md` (kind layers),
   every step conditional.
3. Author the playbook repo's own `.claude/command-profile.local.md`.
4. `compose-claude.sh`: copy `packs/<pack>/command-profile.md` → `$TARGET/.claude/command-profile.md`
   if present; keep the existing scalar marker substitution for iOS.
5. Retarget the inbox/`PLAYBOOK_PATH` runtime contract to `$PLAYBOOK_HOME` across `inbox.md`,
   `conform.md`, `upgrade.md`, `core/rules/playbook-inbox.md` (it's parsed by those consumers,
   not just substituted — see hazy-dreaming steps 5–7).
6. Make `conform.md` Check C pack-aware: only expect the six iOS bootstrap commands when iOS-pack
   rules are present (heuristic: `.claude/rules/build-deploy.md` exists).
7. `git rm` `.claude/templates/commands/{status,wrapup}.md` (superseded). Update `packs/README.md`.
8. **Gates:** (a) byte-identical compose for every unchanged iOS artifact — only `status`/`wrapup`
   differ and a new `command-profile.md` appears; (b) lossy-extraction diff per the coverage table.

**Phase B — non-iOS symlink bridge (after A is on `main`; one PR per repo, branch off `main`).**
Build `bridge-symlink.sh <target>` (surgical: never `rm -rf .claude/`, never touch
`settings.local.json`). Then:
- **devpulse** (clean — no `.claude/`, Python): symlink skeleton + `core/rules` +
  `packs/python/command-profile.md`. One-line CLAUDE.md note on relinking. Smoke-test `/status`.
- **shotsmith** (Python): `git rm` the three bespoke commands; symlink; add the 3-line
  `project.yml` above. CI (`test.yml`) ignores `.claude/`, unaffected.
- **c3d** (kind-of-one): `git rm` the two bespoke commands; symlink skeleton + `core/rules`;
  author `.claude/command-profile.local.md` (fix the stale `docs/scope.md` → root `scope.md`).

**Phase C — generalize on contact.** As `/context-health`, `/preflight`, `/test` next need a
touch, convert each to skeleton + `## /<verb>` section. No big bang.

**Later — Stage 3.** Port the dynamic verbs to MCP tools reading `project.yml`; keep
`command-profile.md` as the per-kind prose the tools fold in.

## Out of scope / deliberately not doing

- **No config language.** `project.yml` is a handful of flat keys, no logic. If a fact wants
  logic, it's prose in `command-profile.md`.
- **No pack for a kind-of-one** until a second instance exists. c3d stays in
  `command-profile.local.md`.
- **Don't rip out the iOS markers.** `__PRIMARY_SIM__` etc. keep working at compose time;
  `project.yml` is the forward path, adopted lazily, not a forced migration.
- **Don't re-touch the merged iOS apps' pinned submodules** this round — they re-pin in Stage 1b.

## Related cleanup (DONE — rules pass, 2026-06-01)

`core/rules/git-workflow.md` used to leak iOS assumptions into a *core* rule — `[skip ci]`
local/cloud, "update Current State in CLAUDE.md," `globs: **/*.swift`, a `dev`-centric branch
model, a `ui` commit type, mandatory `WORKLOG` / `release-notes-draft`. Same disease (kind
knowledge in a universal file), and Phase B's non-iOS symlink bridge made the leak live in
devpulse / shotsmith / c3d. **Fixed in the rules pass (2026-06-01):** the rule is now universal
(`globs: **/*`, `main` + `feature/*`/`fix/*` with `dev` optional, generic commit types) and its
session-end record steps were deferred to `/wrapup` + each project's `command-profile` — the iOS
profile already owned `[skip ci]` and release notes, so this was mostly deletion, no new
`packs/ios/` rule needed. Gates: iOS compose still carries every git behavior (relocated to the
profile); the live symlink in all three non-iOS repos now serves the cleaned rule. The bridge keeps
linking the whole `core/rules/` unchanged — making the rule truly core was the right fix, not
special-casing the bridge. The latent **`packs/<pack>/rules` loop** in `bridge-symlink.sh` stays
deferred: no non-iOS pack has a `rules/` dir yet, so there was nothing for the loop to link.
