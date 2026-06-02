# Playbook structure: `core/` + `packs/`

Rules and commands are organized into layers a project composes, instead of
one flat iOS-only set:

- **`core/`** — universal, language-agnostic. Every project gets these.
- **`packs/ios/`** — Apple-platform (Swift / Xcode / fastlane / ASC / screenshots).
- **`packs/python/`, `packs/cli/`** — placeholders for non-iOS stacks (filled in as needed).

`bootstrap.sh` assembles a project's `.claude/rules/` from `core/` **+** the relevant
pack(s), its `.claude/commands/` from the pack(s) **+** the universal commands in
`.claude/commands/`, and the pack's `command-profile.md` into `.claude/`. Today bootstrap
targets iOS, so it composes `core` + `ios`: all 16 rules and 14 commands land in the project,
plus the iOS `command-profile.md`, with the `playbook-inbox` path substitution and
`__PRIMARY_SIM__` marker intact. (`/status`, `/wrapup`, and `/test` are now universal skeletons
that load the profile at runtime — see "Command profiles" below.)

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
| `packs/ios/commands/` | feature, gen-tests, review, deploy, release, preflight |
| `.claude/commands/` (universal) | capture-manual-surfaces, conform, context-health, inbox, status, test, upgrade, wrapup (+ `curate`, playbook-only) |

## Command profiles — universal `/status` + `/wrapup` (Phase A, 2026-06-01)

`/status` and `/wrapup` are single **universal skeletons** in `.claude/commands/` — the same
file every project runs. Kind- and project-specific behavior is layered on at runtime via a
profile the skeleton loads; the command file is never forked. Three tiers + an escape hatch
(full rationale in [`../COMMANDS-ARCHITECTURE.md`](../COMMANDS-ARCHITECTURE.md)):

| Tier | File | Owner | Carries |
|---|---|---|---|
| Universal skeleton | `.claude/commands/{status,wrapup,test}.md` | playbook | the invariant verb, platform-agnostic |
| Kind layer | `packs/<kind>/command-profile.md` | playbook | everything common to a project *type*; every step conditional |
| Instance facts | `.claude/project.yml` (optional) | project | declarative facts a command can't detect |
| Escape hatch | `.claude/command-profile.local.md` (optional) | project | prose judgment for a kind-of-one |

`compose-claude.sh` copies `packs/<pack>/command-profile.md` → the project's
`.claude/command-profile.md` alongside the rules and commands; a project's own
`command-profile.local.md` is project-owned and never composed. The retired downstream
`/status` + `/wrapup` template variants (`.claude/templates/commands/`) are gone — the
skeleton plus the profile replaces them.

**`/test` joined them in Phase C (2026-06-01)** as a universal *run-the-declared-suite* verb:
it runs `project.yml` `test_command` or the kind profile's default (`pytest -q` for Python,
`xcodebuild test` for iOS) and no-ops cleanly where there's no runner. The old iOS `/test`
*generated* Swift Testing tests — a different verb — so it was renamed to the iOS-pack
`/gen-tests`, leaving the `/test` name for the runner the way `npm test` / `cargo test` mean it.
(`capture-manual-surfaces` is iOS-specific per §5 but still lives in `.claude/commands/`; it can
move to the ios pack in a later tidy-up.)

The full classification — every rule and command mapped to core-skill / ios-skill /
always-on-stub / mcp-tool / reference-Hudson / delegate-Kickstart — is in
[`../REFACTOR-PLAN.md`](../REFACTOR-PLAN.md) §5.
