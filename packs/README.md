# Playbook structure: `core/` + `packs/`

Rules (and, soon, commands) are organized into layers a project composes, instead of
one flat iOS-only set:

- **`core/`** — universal, language-agnostic. Every project gets these.
- **`packs/ios/`** — Apple-platform (Swift / Xcode / fastlane / ASC / screenshots).
- **`packs/python/`, `packs/cli/`** — placeholders for non-iOS stacks (filled in as needed).

`bootstrap.sh` assembles a project's `.claude/rules/` from `core/` **+** the relevant
pack(s). Today bootstrap targets iOS, so it composes `core` + `ios` — and the downstream
output is identical to before the carve (all 16 rules still land in the project's
`.claude/rules/`, with the `playbook-inbox` path substitution intact).

## Rules carved (Stage 1a, 2026-05-30)

| Layer | Rules |
|---|---|
| `core/rules/` | session-health, git-workflow, work-log, assertion-discipline, manual-tasks, playbook-inbox |
| `packs/ios/rules/` | asc-troubleshooting, build-deploy, code-style, legal-urls, metadata-translation, privacy-manifest, screenshot-pipeline, status-bar-overrides, testing, wwdc25-ios26 |

Still to carve (next increments): commands (incl. the iOS command heredocs currently
inline in `bootstrap.sh`), then the project-side **bridge** (symlink for Python utils,
submodule for iOS apps) and **de-bootstrap** of existing projects.

The full classification — every rule and command mapped to core-skill / ios-skill /
always-on-stub / mcp-tool / reference-Hudson / delegate-Kickstart — is in
[`../REFACTOR-PLAN.md`](../REFACTOR-PLAN.md) §5.
