# Playbook structure: `core/` + `packs/`

Rules and commands are organized into layers a project composes, instead of
one flat iOS-only set:

- **`core/`** — universal, language-agnostic. Every project gets these.
- **`packs/ios/`** — Apple-platform (Swift / Xcode / fastlane / ASC / screenshots).
- **`packs/python/`, `packs/cli/`** — placeholders for non-iOS stacks (filled in as needed).

`bootstrap.sh` assembles a project's `.claude/rules/` from `core/` **+** the relevant
pack(s), and its `.claude/commands/` from the pack(s) **+** the universal commands in
`.claude/commands/`. Today bootstrap targets iOS, so it composes `core` + `ios` — and the
downstream output is identical to before the carve (all 16 rules and 13 commands still
land in the project, with the `playbook-inbox` path substitution and `__PRIMARY_SIM__`
marker intact).

## Rules carved (Stage 1a, 2026-05-30)

| Layer | Rules |
|---|---|
| `core/rules/` | session-health, git-workflow, work-log, assertion-discipline, manual-tasks, playbook-inbox |
| `packs/ios/rules/` | asc-troubleshooting, build-deploy, code-style, legal-urls, metadata-translation, privacy-manifest, screenshot-pipeline, status-bar-overrides, testing, wwdc25-ios26 |

## Commands carved (Stage 1a, 2026-05-31)

The six iOS command heredocs moved out of `bootstrap.sh` into files; bootstrap now copies
them like rules. Universal commands still live in `.claude/commands/` (with downstream-only
`/status` + `/wrapup` variants in `.claude/templates/commands/`).

| Layer | Commands |
|---|---|
| `packs/ios/commands/` | feature, test, review, deploy, release, preflight |
| `.claude/commands/` (universal) | capture-manual-surfaces, conform, context-health, inbox, status, upgrade, wrapup (+ `curate`, playbook-only) |

Still to carve (next increments): the project-side **bridge** (symlink for Python utils,
submodule for iOS apps) and **de-bootstrap** of existing projects. (`capture-manual-surfaces`
is iOS-specific per §5 but still lives in `.claude/commands/`; it can move to the ios pack
in a later tidy-up.)

The full classification — every rule and command mapped to core-skill / ios-skill /
always-on-stub / mcp-tool / reference-Hudson / delegate-Kickstart — is in
[`../REFACTOR-PLAN.md`](../REFACTOR-PLAN.md) §5.
