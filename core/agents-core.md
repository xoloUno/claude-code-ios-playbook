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
  say so and suggest a fresh session. When autonomy applies, commit checkpoints to the task
  branch and push it; otherwise preserve work without committing or pushing automatically.
- Before committing code changes, run the project's applicable declared validation gates.
  Use its test workflow when there is one, otherwise the documented test command. Report
  failures, blockers or an unconfigured runner, and never claim that skipped checks passed.

### Autonomy
- This section applies only in Claude Code sessions, and only when
  `~/.config/playbook/config` sets `PLAYBOOK_AUTONOMY=on` and `.claude/project.yml` doesn't
  set `autonomy: off`. Otherwise commit, push and merge only when the user asks; running
  `/wrapup` asks for a commit, a push and a PR.
- Don't ask about routine work. Commit to a task branch, push feature branches, open and
  update your own PRs, and merge a PR that meets the checklist below, then delete its branch.
- Merge checklist:
  - the work is finished, not a checkpoint;
  - the project's tests and lint pass on the PR's latest commit;
  - if the repo has CI, at least one check ran on that commit and every check passed, so
    leave `[skip ci]` off the last push;
  - the branch contains the current `main`;
  - after one local Codex review, no open finding meets the bar in "Code Review Rules".
    That review is the merge review: run it on the PR's changes as "Second opinions" says,
    and don't wait for the GitHub Codex bot. Fix each finding that meets the bar, including
    any the bot has posted by then, and don't ask for another review afterward. A PR that
    changes only prose needs no Codex review, though publishing it still needs the user. It
    isn't prose-only if it touches `AGENTS.md`, `CLAUDE.md`, `.claude/`, hooks, workflows or
    code, or, in the playbook, `core/` or `packs/`;
  - nothing in the PR needs the user (next bullet).

  For playbook shared source, `pytest` must also pass, and a compose diff must show only
  the intended downstream changes. If any item fails, park the PR.
- These always need the user:
  - device testing;
  - App Store Connect and Developer Portal actions;
  - force pushes, history rewrites, and deleting unmerged branches;
  - tags and releases;
  - publishing something live, meaning a push or merge that deploys a site or changes files
    a live site serves;
  - repo settings, secrets and credentials;
  - money, and messages to people;
  - changes to guardrails (this section, permission settings, hooks), deploy workflows or
    signing;
  - new dependencies;
  - material departures from the agreed request;
  - anything irreversible, such as discarding uncommitted work, deleting files you didn't
    create, dropping a stash, or wiping simulator or database data.

  Park these instead of stopping.
- On public repos, check PR titles, descriptions, comments and attachments for personal
  details and secrets before posting them.
- Never stop on a question. Ask once with your recommendation, park it, and keep doing
  independent work. When only parked items remain, send one notification and end the turn.

### Second opinions
- In Claude Code, get one local Codex review before building a plan with several moving
  parts, and after two failed attempts at the same problem. Write the prompt to a temp file,
  ask Codex to apply "Code Review Rules", then, from the repo, run
  `"$PLAYBOOK_HOME"/tools/codex-review.sh <prompt-file> <name>`, resolving `PLAYBOOK_HOME`
  as "Playbook lessons" says. One round; its findings are inputs, not approvals. The merge
  review in "Autonomy" runs the same command.

### Handoffs and records
- Anything that needs the user goes in `MANUAL-TASKS.md` at the repository root, not only in
  chat. That covers human-only tasks (store or portal UIs, repository settings, physical
  devices, logins), approvals and decisions. Check first that you can't do them yourself.
  - Append under a dated heading, group by destination, give exact navigation paths and
    values, keep outstanding items from earlier sessions, and note prerequisites.
  - Mark each item `approve`, `do` or `decide`, and say what it blocks. Give an `approve`
    item the commit or build it applies to.
- At session start, list unchecked `MANUAL-TASKS.md` items first, and ask whether they're
  done before starting work that depends on them.
  - An approval covers only its item, at that commit or build. If the target moved, park it
    again.
  - Marking a `do` item done reports a manual step; it never authorizes an action.
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

### Grok Bot
- "Grok Bot" is xAI and Cursor's computer-use agent. It operates a real browser on a
  Cursor-hosted cloud computer, in accounts the user signs it in to. It is not the Grok
  chatbot. A "Grok Bot prompt" is a paste-ready task for a website's UI (App Store Connect,
  the Developer Portal, GitHub settings, any web console), not a research hand-off.
- When asked for one, write it even if you could do the task yourself, and name any API or
  CLI route in one line. Give it as one fenced block, in your reply and under its
  `MANUAL-TASKS.md` item, complete without this conversation:
  - the goal, what it may touch, identifiers (app, bundle ID, version, build) and the
    starting URL;
  - numbered steps with exact navigation paths, field names and values, and conditions such
    as "only if offered";
  - "stop, screenshot and report" for any screen that doesn't match the steps;
  - "ask me before clicking <button>" ahead of each irreversible click (submit, publish,
    delete, pay), with an exact readback first of any value that can't change once saved
    (an SKU, a product ID);
  - what to report when done.
- Leave sign-in, 2FA and payment to the user. Keep secrets out: the prompt goes to xAI and
  Cursor.
- When the user says it's done, check the result through an API or CLI where one exists,
  such as the App Store Connect API for version state, build and review submission, and say
  what you checked.

### Playbook lessons
Capture new reusable lessons promptly in the shared playbook inbox. Resolve `PLAYBOOK_HOME`
from the environment or from `~/.config/playbook/config`, then append an entry to its
existing `inbox.md` in the format its header gives. Leave out project-only details, lessons
already documented, and one-off failures. If the directory or the inbox is missing, report
it instead of creating a guessed destination.

## Code Review Rules
- Report only findings that could lose data, publish something private, do something
  irreversible, or break a routine workflow (build, test, commit, push, PR, merge, release).
- Leave out style, naming, wording, and risks that need an unlikely setup.
- Suggest the smallest fix, and prefer removing code over adding machinery.
