# Contributing

Thanks for your interest in improving the playbook. This project is built from real iOS shipping experience with Claude Code.

## How to contribute

1. **Fork** the repo and create a branch from `main`
2. **Make your changes** — follow the conventions below
3. **Submit a pull request** with a clear description of what changed and why

## Conventions

- **No PII.** This repo is public. Use generic placeholders (`YOUR_TEAM_ID`,
  `com.example.*`, `you@example.com`, `YourOrg`) — never real credentials,
  names, emails, or org names. Real values belong in `.env.playbook` (gitignored).
- **Test what you write.** If you add a command, run it first. If you add a gotcha,
  explain how you hit it.
- **Match the tone.** Pragmatic, operational, direct. Explain *why* when a decision
  matters. No academic abstractions.
- **Keep it scannable.** Use tables for comparisons, code blocks for commands,
  callouts for warnings. If a section is long, consider condensing or splitting it.

## What makes a good contribution

- Bug fixes (broken commands, outdated tool versions, wrong paths)
- New gotchas that cost you >1 hour to figure out
- Tool updates (new versions, deprecations, better alternatives)
- Missing steps that tripped you up as a new user
- Condensing verbose sections without losing information

## What to avoid

- Adding features you haven't personally used in a shipping project
- Speculative "nice to have" sections — wait until the need is real
- Rewriting working sections for style preferences
- Adding third-party UI libraries or non-standard tooling

## CHANGELOG

When adding new content, add a dated entry to `CHANGELOG.md` in the existing
format: what changed, which files, and how to upgrade existing projects.
