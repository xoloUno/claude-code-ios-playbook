## Shared workflow (playbook core)

This section is generated. Change its source in the playbook rather than editing it here.

### Verify before asserting
For claims that are costly to get wrong, check in this session instead of recalling. That
covers store or platform behavior (accepted image sizes, alpha, review rules), service and
tool behavior (read the installed source, query the API, or try it), and device or simulator
capabilities. Before recommending a change to repository visibility or hosting tier, verify
the target repository, its current visibility, and the relevant hosting configuration and
plan restrictions. Verifying them is not authorization to change them.

### Git
- Don't commit directly to the protected default branch (usually `main`). Use a task branch
  and a PR, following the project's branch-naming and integration-branch conventions.
- Commit by logical change, not by file count, as `type(scope): description`. Types are
  `feat`, `fix`, `refactor`, `chore`, `docs` and `test`, and project or pack conventions may
  add more. Keep the subject at 72 characters or less, in present tense, with no trailing
  period.
- Stage explicit paths. Never `git add .` blindly.
- Attribution follows the host's settings and the user's policy. Don't hardcode a
  co-author line.
- Parallel agent sessions in one repository each get their own worktree.

### Session hygiene
- At session start, inspect existing changes. Preserve work you didn't make and carry on
  with independent work. Ask before altering, committing or stashing unrelated changes.
- Checkpoint at logical milestones. If repeated mistakes suggest the context is degrading,
  say so and suggest a fresh session. Preserve work without committing or pushing
  automatically.
- Before committing code changes, run the project's applicable declared validation gates.
  Use its test workflow when there is one, otherwise the documented test command. Report
  failures, blockers or an unconfigured runner, and never claim that skipped checks passed.

### Handoffs and records
- Human-only tasks (store or portal UIs, repository settings, physical devices, logins) go
  in `MANUAL-TASKS.md` at the repository root, not only in chat. Check first that you can't
  do them yourself. Append under a dated heading, group by destination, give exact
  navigation paths and values, keep outstanding tasks from earlier sessions, and note
  prerequisites.
- At session start, if `MANUAL-TASKS.md` has unchecked items, ask whether they're done
  before starting work that depends on them.
- When resuming work, read the latest `WORKLOG.md` entry if there is one. At session end,
  follow the project's declared wrapup workflow:
  - if the project uses `WORKLOG.md`, add a dated entry at the top covering what changed,
    decisions and blockers
  - if `AGENTS.md` has a Current State section, give it a brief update in the project-owned
    part
  - keep durable decisions in tracked documentation
  - never edit the generated core during wrapup; `CLAUDE.md` is a symlink to this file, so
    write to `AGENTS.md` itself
- `MANUAL-TASKS.md` and `WORKLOG.md` are local scratchpads. Check the project's ignore rules
  before treating their contents as untracked.

### Playbook lessons
Capture new reusable lessons promptly in the shared playbook inbox. Resolve `PLAYBOOK_HOME`
from the environment or from `~/.config/playbook/config`, then append to its existing
`inbox.md` with the date, project, Category, Context, Lesson and Suggested action. Leave out
project-only details, lessons already documented, and one-off failures. If the directory or
the inbox is missing, report it instead of creating a guessed destination.
