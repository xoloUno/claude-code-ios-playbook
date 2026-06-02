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

## /test

The universal `/test` resolves which command to run; this kind layer supplies the Python
default and how to scope it.

- **Command.** Use `project.yml` `test_command` if declared (the runner is invoked
  **verbatim**, so the declared command must actually run in this environment — prefer
  `python3 -m pytest -q` over a bare `pytest -q` when the `pytest` console script isn't
  guaranteed on PATH). Otherwise default to `python3 -m pytest -q` when a `tests/` directory
  or any `test_*.py` / `*_test.py` file exists. If the project has no tests at all, no-op —
  report that and stop.
- **Scope.** With `$ARGUMENTS`, pass it through as a pytest selector — a path
  (`tests/test_foo.py`), a node id (`tests/test_foo.py::test_bar`), or a `-k <expr>`
  keyword filter.
- **Report.** pytest's own summary line is the verdict; on failure, show the failing node
  ids and the first assertion/error for each.

This is the same runner the `/wrapup` pre-commit gate invokes — `/test` just surfaces it
on demand.

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
  run it — the declared command, or `python3 -m pytest -q` by default — when Python source
  changed. (Same runner `/test` invokes; `python3 -m` form survives a missing `pytest`
  console script.) Failures must be fixed or explicitly acknowledged before the commit. This is a *gate*:
  it runs after the record mutations above and before staging/commit, so a red test can
  still stop the commit.
