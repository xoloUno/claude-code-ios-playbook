# _playbook — operating guide for this repo

`_playbook` is the source of truth for the shared Claude Code / Codex rules, commands, and
scaffolding distributed to every project under `~/dev`. It's a docs-and-tooling repo: no app,
no build, no test suite. The deliverable is the shared source other repos consume.

**Prime directive: kill drift.** Every fact has exactly one home. When something must differ
per project, that's a *layer*, not a copy — never fork a shared file to make a local change.
This repo exists because the old bootstrap-and-copy model let four `/status` variants drift
apart.

## Dream state

This is a low-maintenance agentic coding harness for `~/dev`: Erik can create a project on a
whim — a one-off repo like shotsmith/devpulse/c3d, or a bootstrapped iOS app — and it should
inherit the shared workflow surface without re-deriving commands, rules, or lessons. Universal
verbs live once; kind behavior extends through packs/profiles; project facts stay tiny.
Battle scars flow `/inbox` → `/curate` → `_playbook` once, then propagate automatically where
the bridge allows it: live symlinks for non-iOS repos, controlled compose/marketplace rollout
for iOS. Judge new work by whether it reduces tool/wisdom drift, shrinks per-project upkeep,
and keeps project-owned files outside auto-clobber boundaries unless they have an explicit
managed-block contract.

## Invariants (do not violate)

- **Correctness-critical rules live flat in the always-on stub** (`CLAUDE.md` / `AGENTS.md`),
  never behind skill progressive disclosure — disclosure does not transfer across agents
  (Claude and Codex each decide when to load `references/`).
- **`CLAUDE.md` and `AGENTS.md` (Stage 3) are generated from one source** — two stubs
  hand-maintained in parallel would drift. Not yet true; honor it when stub emission begins.
- **Every vendored dependency is pinned and degrades to a no-op** if it vanishes (Hudson gone →
  run the fork; Kickstart gone → lose a convenience, not a capability).
- **Dynamic verbs become MCP _tools_, not prompts** (Codex doesn't surface MCP prompts).
- **Byte-identical compose is an acceptance gate.** A change to shared source must leave the
  composed downstream output unchanged except where the change intends it — verify with a
  compose diff before merging.

## Map

- `core/` — universal rules (every project gets these). `packs/{ios,python,cli}/` — per-kind
  rules + commands.
- `compose-claude.sh` — assembles a project's `.claude/` from `core/` + a pack. Shared by
  `bootstrap.sh` (new projects) **and** the submodule bridge (existing iOS apps) so the two
  paths can't drift.
- `bridge-symlink.sh` — the symlink counterpart: links a non-iOS repo's `.claude/` (core
  rules + the universal commands + an optional pack `command-profile.md`) back into this tree
  with relative symlinks. No compose step, no pin — always the current shared source. Surgical
  and idempotent; never overwrites a real file or a project-owned `settings.local.json` /
  `project.yml` / `command-profile.local.md`.
- `bootstrap.sh` — scaffolds a brand-new iOS project. `CLAUDE-TEMPLATE.md` → the downstream
  project's `CLAUDE.md` (not this file).
- **Bridges:** iOS apps = pinned submodule + composed copies (`compose-claude.sh`); non-iOS
  repos = live symlinks into this tree (`bridge-symlink.sh`).
- `$PLAYBOOK_HOME` (`~/.config/playbook/config`) is the runtime pointer; `/inbox`, `/conform`,
  `/upgrade` resolve through it. `inbox.md` aggregates captured lessons centrally; `CHANGELOG.md`
  is the contract downstream `/upgrade` reads.

## Where things live

- **Status + next steps:** `REFACTOR-PLAN.md` — canonical, read it first. This file carries
  principles only and deliberately holds no status, so the two can't drift.
- **Commands architecture:** `COMMANDS-ARCHITECTURE.md` — the universal-skeleton + kind-pack +
  instance-facts model the command refactor follows.
- **Session backup:** auto-memory under `~/.claude/.../memory/` mirrors the plan and loads each
  session.

## Working norms

- Never push `main`; branch and open a PR. Commit with **explicit pathspecs** — the working
  tree often carries an unrelated dirty `inbox.md` from another session; never stage it blind.
- **Status changes go in one place:** keep `REFACTOR-PLAN.md` current when a decision changes;
  don't restate status here.
- This root `CLAUDE.md` is **not** distributed: neither `compose-claude.sh` nor `bootstrap.sh`
  copies it. Edit freely; it stays local to the playbook.

## Out of scope unless asked

Deferred boundaries — don't start these unprompted; each is tracked in `REFACTOR-PLAN.md`:

- **Deleting the iCloud rollback copies** — HELD, irreversible (§0); only on Erik's explicit go.
- **Spinning out PlaybookLauncher** — Stage 4.
- **Adopting Hudson / Kickstart** beyond the staged plan — Stage 2 / Decision B.
- **Codex + MCP implementation** before the Claude bridge is stable — Phase 2/3.
