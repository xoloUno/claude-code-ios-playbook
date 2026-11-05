# Delegating implementation to a local agent

Claude Code orchestrates; another local agent writes bounded code. Distilled from Kendibah's
delegation batches (2026-10-28 → 11-02: Cursor's CLI on `grok-4.7-xhigh-fast`, and
`codex exec`). Model names and quotas change; the roles and the brief don't.

## Roles

- **Claude** plans, writes the briefs, keeps concurrency machinery and new Apple APIs, builds
  and tests every delegate's work, commits, opens PRs and merges.
- **Delegates** write bounded code, each in its own git worktree outside the repo.
- **The merge review** (core "Second opinions") runs before every merge. Green delegate tests
  caught none of the defects merge reviews found in eight of nine PRs.
- Default implementation to Cursor and keep Codex for reviews when the Codex quota is tight.

## Before the briefs: review the plan

Run one `codex-review.sh` pass on the written plan right before delegating. On batch 4 it
found six design gaps; with them written into the briefs, all three delegates passed on the
first run and the merge reviews found one defect. Put each finding into the brief as a
requirement, with the test that proves it.

## The brief

- The exact files to edit, and a ban on everything else. Unprompted, a delegate hand-edited
  `project.pbxproj` in an XcodeGen project, and `.swiftlint.yml`.
- The existing pattern to copy.
- Required tests, including error, cancellation and race paths.
- The exact build and test command, on a simulator UDID reserved for that task.
- No git, `gh`, network or device traffic.
- No closure parameters with typed `throws(E)` (Cursor shipped one that didn't compile).
- A reply listing the files changed, test counts and doubts.

## Launch recipes

**Cursor** (about 13 minutes per task; two in parallel worked):

```bash
cd <worktree> && cursor-agent -p --trust --workspace "$PWD" --model <model> "<brief>"
```

- Put a `.cursor/cli.json` allowlist in the worktree permitting only `xcodebuild`,
  `xcodegen` and `swiftlint`. It loads from the working directory, not from `--workspace`,
  so `cd` first; otherwise the global config applies.
- Pass neither `--force` (auto mode blocks it as an unsafe agent) nor `--sandbox` (Cursor
  then can't build, and two of four sandboxed tasks came back with compile errors).
- Launch it from Claude Code, not from inside another agent's sandbox: a nested agent
  inherits its parent's sandbox. Started from inside Codex, every command came back
  "Rejected:" with no reason. Treat "Rejected:" as "nothing ran".

**Codex** (about 3 minutes per task; compiled and passed first time):

```bash
codex exec -C <worktree> -s workspace-write -m <model> -c model_reasoning_effort=high \
  -o <last-message-file> "<brief>"
```

It can't build inside its sandbox (`~/.cache/clang/ModuleCache: Operation not permitted`),
and it spends the quota the merge reviews need.

## Orchestrator chores

- Run what the delegate couldn't. Building catches its compile errors; only running against
  the real OS or network catches the rest (a Grok review of Grok code missed four runtime
  bugs). Use a macOS harness where the Simulator can't help (see `simulator.md`).
- Regenerate the project with `xcodegen` in a clean worktree. Resolve `project.pbxproj`
  conflicts between delegate branches with `git checkout --theirs` plus `xcodegen generate`,
  never by hand.
- Delete the delegates' DerivedData, and stage explicit paths (never `.cursor/`).
- After each merge, merge `main` into the next branch, re-test and push. Those sequential CI
  rounds are the slowest part, so batch related work into fewer PRs.
- Serialize your own `xcodebuild` test runs: three in parallel pushed one past 10 minutes.
- Record each batch's first-run pass rate, to see whether the briefs are improving.
