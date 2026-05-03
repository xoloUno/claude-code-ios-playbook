# Playbook Inbox

Lessons learned, gotchas, suggestions, and patterns discovered during Claude Code
sessions across all projects. Entries are written automatically by sessions in other
project directories. Periodically review this file in a dedicated playbook session to
curate worthwhile additions into the playbook, templates, or rules.

## How entries get here

Each bootstrapped project has a `.claude/rules/playbook-inbox.md` rule that tells
Claude Code to append entries here when it discovers something worth capturing.

## Curation process

In a Claude Code session in the `_playbook/` directory:
1. Read this file
2. For each entry, decide: **adopt** (update playbook/template/rules), **defer**, or **discard**
3. Adopted entries → make the change, then delete the entry
4. Deferred entries → leave them for next review
5. Discarded entries → delete them
6. If all entries are processed, leave only this header

## Entry format

```markdown
### [DATE] — [PROJECT_NAME]

**Category:** gotcha | suggestion | pattern | correction | tooling
**Context:** [what was being done when this was discovered]
**Lesson:** [the actual insight — be specific]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

---

### 2026-04-27 — HVACApp

**Category:** pattern
**Context:** HVACApp is an internal-team field-ops app distributed via
TestFlight to a small group, never to the public App Store. Its app shape
is meaningfully different from the playbook's assumed solo-dev-public-app:
a single shared iCloud account across team devices, a `Device` @Model
registry, session switching with passcode protection for elevated roles,
role-based access (Owner/Manager/Technician), no StoreKit, no public app
icon urgency, no marketing screenshots, no privacy/terms hosting needed.

**Lesson:** "Internal/team-distributed app" is a distinct archetype the
playbook doesn't currently address. The playbook templates and slash
commands assume public-App-Store-bound apps (StoreKit setup as Phase 2,
detailed App Store metadata + screenshot + privacy hosting in Phase 5-6).
For internal apps, large chunks of the playbook are skippable, and other
patterns (multi-user session management, device registry, role-based
access, TestFlight-only distribution) are essential but unaddressed.

**Suggested action:** Add a dedicated section to `ios-project-playbook.md`
— maybe "Phase 8: Internal/team apps" or fold into Phase 4. Cover:
- Session manager + device registry pattern (HVACApp's `SessionManager`
  + `Device` @Model is a good reference)
- Role-based access (Owner > Manager > Technician permission ladder)
- Passcode-protected session switching (CryptoKit salted SHA-256)
- TestFlight-only distribution flow (no /release lane needed)
- Reactive `currentUser` from session store (computed property pattern,
  not stored `let` parameter)
- ChangeLog audit trail conventions
Also: `.env.project` could grow a `DISTRIBUTION_MODE=public|internal|enterprise`
that drives whether `/release`, `appshot`, `docs/legal` get installed.

---

### 2026-04-27 — HVACApp

**Category:** pattern
**Context:** Mid-session, Erik asked to design a parallel-agent
worktree workflow: (1) coordinator decomposes work into N independent
tasks, (2) creates `.worktrees/task-NN` per task, (3) spawns Task agents
in parallel via `run_in_background: true`, (4) opens PRs for green ones,
(5) merges and cleans up worktrees. Implemented as
`.claude/rules/parallel-worktrees.md` + `.claude/commands/parallel-tasks.md`
in HVACApp.

**Lesson:** For multi-file refactors with N truly independent tasks
(SwiftLint cleanup across 30+ files, multi-platform build verification,
adding tests for N independent modules), worktree-parallelism with
background agents is a real efficiency multiplier. Each agent works in
isolation in its own checkout, can build/lint/test what it changed, and
opens a PR. The coordinator polls completions (no sleep/poll — runtime
notifies on background agent completion), then squash-merges greens and
surfaces reds for triage. Cap at 8 to avoid CI rate-limits and disk
exhaustion (~500MB per worktree with DerivedData).

NOT a fit for: cohesive single-feature changes, sequential dependencies,
quick (<10 min) work where setup overhead dwarfs savings, tasks that
edit the same file (merge conflicts).

**Suggested action:** Port the pattern to the playbook as a stock
slash command + rule. The slash command (`/parallel-tasks`) takes a
markdown task spec file with allow-lists and forbid-lists per task,
validates non-overlap, spawns agents, manages PR lifecycle, runs
preflight on main. Worth a section in `ios-project-playbook.md` Phase 3
(Development Conventions) covering when to reach for this vs sequential
edits. The HVACApp implementation is at
`/Users/erikj/Documents/JJ AIR/99-WIP/erik/App/HVACApp/.claude/{rules,commands}/parallel-*`
— copy verbatim or refine.

### 2026-05-03 — Playbook (`/wrapup` skill improvements)

**Category:** suggestion
**Context:** End-of-session `/wrapup` ran in the playbook repo itself
(not a typical iOS project). Two friction points surfaced that the
current `/wrapup` skill at `.claude/skills/wrapup.md` (or wherever the
template lives) doesn't handle gracefully.

**Lesson:**

1. **`/wrapup` step 10 says "Push to `dev` or feature branch (not
   `main` unless the user explicitly asks)" — but the safer default
   when the user is ON `main` should be "create a feature branch
   automatically and open a PR", not "ask the user."** When the user
   typed `push` in response to a "want me to push?" question, the
   model interpreted that as "push to main" and the action got blocked
   by the playbook's own `git-workflow` rule (which is enforced via
   the `.claude/settings*.json` permission system). The system's
   denial reason was specific and useful: *"'push' is not specific
   authorization for the default branch."* The fix saved a bad push
   but it surfaced that `/wrapup` should have routed to the PR flow
   from the start. Auto mode was active, which sharpens this — the
   skill should "prefer action over planning" by automatically
   creating a feature branch + PR when on `main`, not asking.

2. **`/wrapup` steps 5–9 (CLAUDE.md "Current State", `WORKLOG.md`,
   `release-notes-draft.md`, scope items, `MANUAL-TASKS.md`) don't
   apply to the playbook repo itself.** Those files are project
   conventions, not playbook conventions — the playbook's CHANGELOG
   is the equivalent of "Current State" + release notes for downstream
   consumers. The skill currently reads as if it's always running in a
   bootstrapped project. Running `/wrapup` in `_playbook/` requires
   the model to silently skip those steps, which is fine when it
   notices but easy to miss.

**Suggested action:**

Update `.claude/skills/wrapup.md` (or the playbook's `wrapup` skill
source — confirm location) with two narrow changes:

1. **Add a "Branch detection" note before step 10:** *"If the current
   branch is `main`, do not ask whether to push. Create a feature
   branch from HEAD (`feat/<short-slug>` derived from the commit
   subject), push the branch, open a PR, and report the PR URL in
   the final summary. The playbook's own `git-workflow` rule
   forbids direct pushes to `main`; honoring it via PR flow is
   the safer default for any branch-protected repo."* This also
   matches the iOS project rule's spirit even when the user is in a
   different repo with its own protections.

2. **Add a "Repo type detection" guard before steps 5–9:** *"Steps
   5–9 (CLAUDE.md / WORKLOG.md / release-notes-draft.md / scope
   items / MANUAL-TASKS.md) apply to bootstrapped iOS projects. If
   running in the playbook repo itself (heuristic: presence of
   `bootstrap.sh` + `CHANGELOG.md` + absence of `CLAUDE.md`), skip
   those steps and instead ensure the relevant `CHANGELOG.md`
   entry exists for the session's user-facing changes."* The
   playbook is one of likely-many tool repos that don't fit the
   iOS-project mold; a generic skip-when-not-applicable rule is
   probably better than a hard playbook check.

Both changes are scoped for a focused `/wrapup` session — one skill
file edit, no behavior change for the common case (running `/wrapup`
in a bootstrapped iOS project on a feature branch).


