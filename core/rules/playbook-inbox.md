---
description: Write lessons learned and gotchas to the shared playbook inbox
globs: **/*
---

# Playbook Inbox Rule

When you discover something during a session that would improve the playbook, templates,
or rules for future projects, append an entry to the shared playbook inbox file:

**Inbox location:** `$PLAYBOOK_HOME/inbox.md`

## What to capture

- **Gotchas** — something that wasted time and could be prevented with better docs or defaults
- **Patterns** — a reusable approach that worked well and should be standardized
- **Corrections** — something in the playbook/template/rules that turned out to be wrong
- **Suggestions** — improvements to tooling, workflow, or conventions
- **Tooling** — MCP tool tips, Xcode workarounds, fastlane discoveries

## What NOT to capture

- Project-specific details (those go in WORKLOG.md)
- Things already documented in the playbook
- Transient issues (build failures, network blips)

## When to write

Capture the lesson **as soon as you notice it** — don't wait for session end. If the
inbox file doesn't exist or the path is wrong, mention it to the user instead of silently
dropping the lesson.

## Entry format

The inbox file's header owns the format: read its "Entry format" section and follow it.
Append new entries at the bottom of the file, before any trailing whitespace, without a
number (curation numbers them).
