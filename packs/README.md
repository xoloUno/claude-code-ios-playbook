# Playbook structure: `core/` + `packs/`

Rules and commands are organized into layers a project composes, instead of
one flat iOS-only set:

- **`core/`** — universal, language-agnostic. Every project gets these.
- **`packs/ios/`** — Apple-platform (Swift / Xcode / fastlane / ASC / screenshots).
- **`packs/python/`, `packs/cli/`** — placeholders for non-iOS stacks (filled in as needed).

`bootstrap.sh` assembles a project's `.claude/rules/` from `core/` **+** the relevant
pack(s), its `.claude/commands/` from the pack(s) **+** the universal commands in
`.claude/commands/`, and the pack's `command-profile.md` into `.claude/`. Today bootstrap
targets iOS, so it composes `core` + `ios`: all 16 rules and 13 commands land in the project,
plus the iOS `command-profile.md`, with the `playbook-inbox` path substitution and
`__PRIMARY_SIM__` marker intact. (`/status` + `/wrapup` are now universal skeletons that load
the profile at runtime — see "Command profiles" below.)

## Rules carved (Stage 1a, 2026-05-30)

| Layer | Rules |
|---|---|
| `core/rules/` | session-health, git-workflow, work-log, assertion-discipline, manual-tasks, playbook-inbox |
| `packs/ios/rules/` | asc-troubleshooting, build-deploy, code-style, legal-urls, metadata-translation, privacy-manifest, screenshot-pipeline, status-bar-overrides, testing, wwdc25-ios26 |

## Commands carved (Stage 1a, 2026-05-31)

The six iOS command heredocs moved out of `bootstrap.sh` into files; bootstrap now copies
them like rules. The universal commands live in `.claude/commands/`.

| Layer | Commands |
|---|---|
| `packs/ios/commands/` | feature, test, review, deploy, release, preflight |
| `.claude/commands/` (universal) | capture-manual-surfaces, conform, context-health, inbox, status, upgrade, wrapup (+ `curate`, playbook-only) |

## Command profiles — universal `/status` + `/wrapup` (Phase A, 2026-06-01)

`/status` and `/wrapup` are single **universal skeletons** in `.claude/commands/` — the same
file every project runs. Kind- and project-specific behavior is layered on at runtime via a
profile the skeleton loads; the command file is never forked. Three tiers + an escape hatch
(full rationale in [`../COMMANDS-ARCHITECTURE.md`](../COMMANDS-ARCHITECTURE.md)):

| Tier | File | Owner | Carries |
|---|---|---|---|
| Universal skeleton | `.claude/commands/{status,wrapup}.md` | playbook | the invariant verb, platform-agnostic |
| Kind layer | `packs/<kind>/command-profile.md` | playbook | everything common to a project *type*; every step conditional |
| Instance facts | `.claude/project.yml` (optional) | project | declarative facts a command can't detect |
| Escape hatch | `.claude/command-profile.local.md` (optional) | project | prose judgment for a kind-of-one |

`compose-claude.sh` copies `packs/<pack>/command-profile.md` → the project's
`.claude/command-profile.md` alongside the rules and commands; a project's own
`command-profile.local.md` is project-owned and never composed. The retired downstream
`/status` + `/wrapup` template variants (`.claude/templates/commands/`) are gone — the
skeleton plus the profile replaces them.

Still to carve (next increments): the project-side **bridge** (symlink for Python utils,
submodule for iOS apps) and **de-bootstrap** of existing projects. (`capture-manual-surfaces`
is iOS-specific per §5 but still lives in `.claude/commands/`; it can move to the ios pack
in a later tidy-up.)

The full classification — every rule and command mapped to core-skill / ios-skill /
always-on-stub / mcp-tool / reference-Hudson / delegate-Kickstart — is in
[`../REFACTOR-PLAN.md`](../REFACTOR-PLAN.md) §5.
