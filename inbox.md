# Playbook Inbox

Lessons learned, gotchas, suggestions, and patterns discovered during Claude Code
sessions across all projects. Entries are written automatically by sessions in other
project directories. Periodically review this file in a dedicated playbook session to
curate worthwhile additions into the playbook, templates, or rules.

## How entries get here

Each bootstrapped project has a `.claude/rules/playbook-inbox.md` rule that tells
Claude Code to add entries here when it discovers something worth capturing.

## Curation process

In a Claude Code session in the `_playbook/` directory:
1. Read this file
2. Give each unnumbered entry the next entry number (below), raising the counter each time,
   then sort all entries newest first, with higher numbers first on the same date
3. For each entry, decide: **adopt** (update playbook/template/rules), **defer**, or **discard**
4. Adopted entries → make the change, then delete the entry
5. Deferred entries → leave them for next review
6. Discarded entries → delete them
7. If all entries are processed, leave only this header

## Entry format

**Next entry number:** 22

Capturing sessions append new entries at the bottom of this file without a number; curation
numbers them. Numbers are permanent IDs: never renumber an entry or reuse a removed number,
and keep the counter when the inbox is empty. Use the IDs when discussing entries. A numbered
entry's heading reads `### #[NUMBER] — [DATE] — [PROJECT_NAME]`.

```markdown
### [DATE] — [PROJECT_NAME]

**Category:** gotcha | suggestion | pattern | correction | tooling
**Context:** [what was being done when this was discovered]
**Lesson:** [the actual insight — be specific]
**Suggested action:** [what should change in playbook/template/rules, or "none — just FYI"]
```

---

### #21 — 2026-10-27 — Flara

**Category:** workflow
**Context:** Submitting an app version to App Review needed App Store Connect web steps: selecting the build, adding the first non-consumable IAP to the version, answering a new age-rating question, and submitting. The owner gave those steps to Grok's computer-use agent instead of clicking through them.
**Lesson:** Pasting Claude's numbered App Store Connect steps verbatim into another agent (Grok) worked on the first try. The agent stopped at an unexpected blocker (an unanswered age-rating question) and reported it with a screenshot. After receiving the follow-up steps, it finished and asked for confirmation before Submit for Review. It also offered to watch the review status and kept app context for next time. What made the steps hand-off ready: exact navigation paths, exact values, "add only if offered" conditions, and the one irreversible click named last. Verify afterwards from the agent's side, not the screenshots: the App Store Connect API (version state, build, `reviewSubmissions` items, IAP state, `ageRatingDeclaration`) confirmed everything.
**Suggested action:** Write MANUAL-TASKS steps for store and portal UIs so they can be pasted into a computer-use agent as-is: navigation path, values, conditional branches, and an explicit "stop and confirm before <irreversible click>". After the agent reports done, add an API verification step to the workflow. A second agent isn't the only route. Claude Code can do the same steps itself, either in the desktop app's built-in browser after the user signs in to App Store Connect, or through the App Store Connect API where an endpoint exists. Each App Store Connect action still needs the user's approval, whichever route is used. Data sent to a third-party agent also goes to that vendor. Choose the route by usage budget. Here the owner keeps a Cursor Pro plan for its separately metered Grok agent; the submission used about 1% of the weekly Grok allowance. That leaves Claude Code and Codex limits for coding and code review.
**Curation (2026-10-27):** deferred. Capture the next Grok (or other agent) hand-off of portal steps too, and formalize a rule only once there is more than one run to go on.
