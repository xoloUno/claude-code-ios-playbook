# Python command profile

Kind-layer extensions for the universal `/status` and `/wrapup`, shared by every
Python project composed from this pack. The universal skeleton loads this file at
runtime and folds each section in at the right stage. **Every step is conditional** —
guarded by a cheap existence check or a fact declared in `.claude/project.yml` — so one
profile serves a rich project (tests + version sync + CHANGELOG) and a bare one (none
of those) without forking: each step simply no-ops when its condition is false.

## /status

Fold these into the briefing after the universal git steps:

- **CI.** If `gh` is available **and** the repo has a workflow (`.github/workflows/*.yml`),
  show the latest run for the current branch:
  `gh run list --branch "$(git branch --show-current)" --limit 1 --json status,conclusion,workflowName`
  → ✅ / ❌ / 🟡. Skip silently if there's no workflow or no `gh`.
- **Version.** If a `VERSION` file exists (or `project.yml` declares `version_files`),
  show the current version and the most recent tag (`git describe --tags --abbrev=0`).
- **Unreleased changelog.** If `CHANGELOG.md` exists and has an unreleased section
  (content above the first `## vN.N.N` / `## [N.N.N]` heading), summarize what's queued.

## /wrapup

Slot these into the universal flow at the stage named — not in list order.

**Record mutations (stage 3 — before staging):**

- **Changelog.** If `CHANGELOG.md` exists and the change is user-facing (new feature,
  behavior/schema/dependency change, breaking change), add an entry. Trivial
  doc/test/internal-refactor commits don't need one.
- **Version sync.** If `project.yml` declares `version_files` and this change bumps the
  version (e.g. a schema-breaking change → major bump), update **every** listed file in
  lockstep (they must not drift) and note it in `CHANGELOG.md`.

**Validation gate (stage 4 — after mutations, before commit):**

- **Tests.** If `project.yml` declares a `test_command` (or a `tests/` directory exists),
  run it — `pytest -q` by default, or the declared command — when Python source changed.
  Failures must be fixed or explicitly acknowledged before the commit. This is a *gate*:
  it runs after the record mutations above and before staging/commit, so a red test can
  still stop the commit.
