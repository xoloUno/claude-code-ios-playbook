# Playbook command profile (local escape hatch)

This repo is a kind-of-one — the playbook source itself, no pack applies. The universal
`/status` and `/wrapup` skeletons load this file at runtime and fold its sections in.
It carries the playbook's own judgment: the CHANGELOG/`Superseded by:` contract that
downstream `/upgrade` reads, the downstream-visible decision, inbox housekeeping, and a
note on which universal steps deliberately no-op here.

## /status

Fold these into the briefing after the universal git steps:

- **Latest CHANGELOG entry** — the playbook's published "current state" for downstream
  `/upgrade` consumers. `grep -m1 '^## ' CHANGELOG.md` → show its date and one-line title
  as a headline.
- **Inbox pending count** — `grep -c '^### ' inbox.md` (each `### ` heading is one
  un-curated lesson). If > 0, mention `/curate` is available.
- **Stale local branches** — `git fetch --dry-run --prune 2>&1` to detect local branches
  whose upstream was deleted (leftovers from a previous session). Report them; don't
  actually prune.

**Steps the universal skeleton's "if present" guards already skip here** (noted so their
absence reads as intentional, not drift): this repo has no `CLAUDE.md` "Current State"
section (its `CLAUDE.md` is a principles-only operating guide — never treat it as a status
doc), no `WORKLOG.md`, no `MANUAL-TASKS.md`, and no `.playbook-version`. It also has no
app dependencies, so there is **no Dependabot** lens — the playbook is a docs-and-tooling
repo with nothing to bump.

## /wrapup

Slot these into the universal flow at the stage named.

**Record mutation (stage 3 — before staging): the CHANGELOG contract.**

- **Decide whether the change is downstream-visible** — i.e. a project bootstrapped from
  this playbook should care. Downstream-visible:
  - `bootstrap.sh` / `compose-claude.sh` changes;
  - anything under `core/rules/` or `packs/*/rules/` (copied into every project);
  - anything under `packs/*/commands/` or `.claude/commands/` **other than** `curate.md`
    (the rest get composed downstream);
  - `packs/*/command-profile.md` (the kind layers now distributed by compose);
  - `CLAUDE-TEMPLATE.md`, `ios-project-playbook.md`, `getting-started.md`;
  - new tools or skills the playbook ships.
  Internal-only (NO CHANGELOG entry): typo fixes in this repo's own
  `status.md` / `wrapup.md` / `curate.md` / `command-profile.local.md`, edits to
  `inbox.md`, `README.md` polish, repo-level metadata, and this root `CLAUDE.md`
  (not distributed).
- **If downstream-visible, add a `CHANGELOG.md` entry** under the `---` separator near the
  top, before prior dated entries. Follow the existing format strictly:
  ```markdown
  ## YYYY-MM-DD — <one-line title>

  <2–4 sentence summary of what changed and why it matters downstream.>

  **Files affected:**
  - `path/to/file.md` — <what changed>

  **What to do in your project:**
  - <concrete adoption steps, or "nothing — only affects newly-bootstrapped projects">
  ```
  If the change retracts or replaces earlier guidance, add the `Superseded by:` /
  `Partially superseded by:` banner under the older entry's `##` heading, per the
  convention at the top of `CHANGELOG.md`.

**Commit (stage 6):**

- Scopes commonly used here: `playbook`, `bootstrap`, `rules`, `commands`, `inbox`,
  `changelog`.
- Do **NOT** append `[skip ci]` — the playbook has no CI lanes that need skipping. (This
  overrides any kind-profile `[skip ci]` guidance; no pack applies here anyway.)

**Inbox housekeeping (after commit):** if this session adopted `inbox.md` entries into the
playbook via `/curate`, confirm `inbox.md` no longer references work that has now landed.

**Steps that no-op here:** there is no `CLAUDE.md` "Current State" to update, no
`WORKLOG.md`, no `release-notes-draft.md`, and no prose-humanizer pass — the playbook
ships docs, not an app, so its session record *is* `CHANGELOG.md` plus the commit history.
