---
description: WORKLOG.md session diary format and rules
globs: **/WORKLOG.md, **/CLAUDE.md
---

# Work Log Rule

`WORKLOG.md` is a **gitignored local scratchpad** that tracks work session-by-session in
reverse chronological order. CLAUDE.md is the reference doc (rarely changes); WORKLOG.md
is the session diary (changes every session).

**Why:** When returning to a project after days or weeks, Claude Code reads the worklog
and resumes work contextually — decisions, blockers, and what changed are all there
without re-reading the entire codebase or git history.

**At session end:** Append a new entry at the top (below the header) with this format:

```markdown
## [DATE] — [Brief description of session focus]

**What changed:**
- [Bullet points of changes made — files, features, fixes]

**Decisions:**
- [Key decisions and rationale — why this approach, what was deferred]

**Blockers:**
- [Open issues, things needing human action, or next-session priorities]
- None. [if nothing is blocked]
```

**Rules:**
- Entries are reverse-chronological (newest first)
- Be specific about files and features changed — future sessions use this to orient
- Record decisions and their rationale — this prevents re-litigating settled questions
- Note blockers even if minor — they become the next session's starting point
- When prior sprints accumulate, condense old entries into a summary section at the bottom
- This file is gitignored — it's a local scratchpad, not project documentation
