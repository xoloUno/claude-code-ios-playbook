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

### 2026-04-09 — Flara

**Category:** gotcha
**Context:** CloudKit E2EE sync — bootstrap used CKQuery to fetch all records on first launch
**Lesson:** CKQuery requires at least one field marked queryable/indexable in the CloudKit Dashboard. Encrypted fields (`encryptedValues`) cannot be indexed. This works silently in Development but fails in Production with "Type is not marked indexable". Use `recordZoneChanges(since: nil)` instead — it fetches all records via change tracking without requiring indexes, and is the correct approach for custom zones with E2EE data.
**Suggested action:** Add to CloudKit section of playbook: "Never use CKQuery with encrypted-only record types. Use recordZoneChanges(since: nil) for initial fetch."

### 2026-04-09 — Flara

**Category:** gotcha
**Context:** CloudKit sync — rapid save() calls (startTracking + updateSeverity) firing concurrent push Tasks
**Lesson:** When multiple mutations happen in quick succession (e.g., user starts a timer then sets severity), each save() triggered a separate background CloudKit push. With `savePolicy: .changedKeys` (last-writer-wins), the stale push could complete last, overwriting the correct value. Fix: debounce pushes — cancel pending push on each save(), wait 500ms for mutations to settle, then push the final state once.
**Suggested action:** Add debounce pattern to CloudKit sync template. Any sync layer that pushes on every local mutation needs debouncing to prevent concurrent push races.

### 2026-04-09 — Flara

**Category:** pattern
**Context:** CloudKit sync — changes not propagating between devices after initial bootstrap
**Lesson:** CKDatabaseSubscription silent push notifications are unreliable, especially on TestFlight/Development builds. Apple doesn't guarantee delivery, deprioritizes them on low battery, and TestFlight environments are flakier. Always include a polling fallback (15-second timer while app is active) alongside silent push. Also add pull-to-refresh on all list views. The delta fetch is cheap — `recordZoneChanges` returns immediately if nothing changed since the last token.
**Suggested action:** Add to CloudKit sync template: "Always implement three sync triggers: (1) CKDatabaseSubscription silent push, (2) periodic polling timer as fallback, (3) pull-to-refresh on main views."

