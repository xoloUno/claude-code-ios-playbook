# Phase C — command generalization, after the rules pass

> **Not the next action.** Per `REFACTOR-PLAN.md` §9 the next work is the **rules pass** (make
> `core/rules/git-workflow.md` truly core — see `RULES-PASS-HANDOFF.md`). **Do not start this Phase C
> before the rules pass is complete, unless Erik explicitly chooses to skip ahead.** This file is a
> working draft kept ready for *that* later phase, not a handoff for the next fresh session.

Continuing the `_playbook` commands refactor. **Phase A is merged** (universal `/status` + `/wrapup`
skeletons + per-kind `command-profile.md`, runtime-bound). **Phase B is merged** (2026-06-01):
`bridge-symlink.sh` + the three non-iOS repos (devpulse, shotsmith, c3d-bridge-modeler) bridged onto
the shared source via live symlinks, and `/conform` Check B made bridge-aware. **Then the rules pass**
(its own handoff). *After that*, Phase C applies the **same Phase A pattern** to the remaining dynamic
verbs — `/context-health`, `/preflight`, `/test` — so each is universal + kind-extensible instead of
forked or iOS-only.

**Phase C is the least pre-locked phase. It is explicitly "on contact, not a big bang"**
(`COMMANDS-ARCHITECTURE.md`): convert a verb when it next needs a touch, and only where
universalizing actually buys something. The investigation below shows the three canonical verbs are
*not* equivalent — read it before deciding scope. Do **not** mechanically lift all three.

**Run from `~/dev/_playbook`. Use sibling repos under `~/dev` only for read-only verification**
(Phase C's commits all land in `_playbook`; the bridged repos inherit universal-command and
`command-profile.md` changes through their symlinks). Read `~/dev/_playbook/CLAUDE.md` first (prime
directive: kill drift; never push `main`; explicit pathspecs — the working tree usually carries a
dirty `inbox.md` from another session, never stage it).

## Orient (read first)
- `~/dev/_playbook/CLAUDE.md` — operating guide + invariants.
- `~/dev/_playbook/COMMANDS-ARCHITECTURE.md` — the three-tier model; the **"Generalization and the
  MCP seam"** section and **Phase C** in Rollout are the charter for this phase. Also the **"Related
  cleanup"** note (the `git-workflow.md` leak) and the Phase B note appended there.
- `~/dev/_playbook/REFACTOR-PLAN.md` §4 (the Phase C line) + §9 (the next-steps, including the two
  rules-pass follow-ups).
- **The model to copy — the merged Phase A artifacts:** `_playbook/.claude/commands/{status,wrapup}.md`
  (universal skeleton + load-first hook) and `packs/{ios,python}/command-profile.md` (per-kind
  `## /<verb>` sections, every step conditional). c3d's `_playbook`-style escape hatch:
  `c3d-bridge-modeler/.claude/command-profile.local.md`.
- Memory: `~/.claude/projects/-Users-erikj-dev/memory/playbook-commands-architecture.md`.

## The pattern (unchanged from Phase A — copy it exactly)
A verb becomes: a **universal skeleton** in `_playbook/.claude/commands/<verb>.md` (platform-agnostic;
opens with the load-first hook that reads `command-profile.md` + `command-profile.local.md` +
`project.yml` and folds in each `## /<verb>` section) **plus** a `## /<verb>` section in each pack's
`command-profile.md` (kind behavior, **every step conditional**) **plus** `project.yml` facts where a
command needs a datum it can't detect. Kinds-of-one use `command-profile.local.md`.

- **Read-only verbs** (`/status`, `/context-health`) may fold profile sections in anywhere.
- **Mutating verbs** keep the load-bearing order (branch route → record mutations → validation gates
  → stage → commit → push). `/test` and `/preflight` are read-mostly gates, but if a conversion adds
  a mutation, honor the order.

## Current state (verified 2026-06-01 — re-verify before acting)
- **Packs:** `packs/ios/` (has `commands/` + `rules/` + `command-profile.md`), `packs/python/`
  (`command-profile.md` only — **no `commands/`, no `rules/`**). **No `packs/cli/` exists yet.**
- **The bridge links exactly five universal commands** — `bridge-symlink.sh` `COMMANDS=(status wrapup
  conform context-health inbox)` — and **`/conform` Check B's non-iOS expected set is the same five.**
  These two are **coupled**: if Phase C makes a verb universal-and-bridged, update **both** (the
  `COMMANDS` array *and* Check B's list) in the same PR, or `/conform` will misreport. This coupling
  is the Phase B lesson — don't relearn it.
- **The three canonical Phase C verbs are not equivalent:**
  - **`/context-health`** — **already universal**, lives in `_playbook/.claude/commands/context-health.md`,
    already bridged to all three non-iOS repos and composed into iOS. It is git-based and
    kind-agnostic. Converting it to skeleton+profile only earns its keep if a *kind-specific* signal
    is wanted (e.g. iOS build-artifact weight, Python `.pytest_cache`/`.venv` size). No bridge/conform
    change needed (it's already in both sets). **Lowest urgency — likely leave until a real signal
    asks for it.**
  - **`/preflight`** — **iOS-pack only** (`packs/ios/commands/preflight.md`): a pre-**deploy** gate run
    before `/deploy` or `/release` (simulators present, ASC character limits, metadata). `/deploy` and
    `/release` are iOS-App-Store verbs the non-iOS repos don't have, so **`/preflight`'s non-iOS value
    is thin.** Options: keep it iOS-pack (honest — it's deploy-coupled), or universalize a *skeleton*
    with a rich iOS profile and only a thin/empty non-iOS lane. **Don't bridge it to non-iOS just to
    be symmetric.**
  - **`/test`** — **iOS-pack only** (`packs/ios/commands/test.md`), and it **generates Swift Testing
    tests** (`Generate Swift Testing tests for $ARGUMENTS`), it does **not run** a suite. It is
    Decision-A-gated (Hudson testing-skill overlap — keep the playbook's voice, *reference* Hudson,
    don't adopt wholesale; full vendoring is Stage 2, out of scope here). So "universal `/test`" is a
    **naming/semantics decision, not a mechanical lift**: a *run-the-suite* verb (maps cleanly to
    `project.yml` `test_command`; useful to shotsmith's pytest) is a **different verb** from the
    existing *generate-tests* command. Decide: rename one, split into two (e.g. run = `/test`,
    generate = `/gen-tests` or keep generation iOS-pack), and only then lift.

## Recommended path (judgment, not locked — adjust per real contact)
There is **no forcing contact** in the tree today, so pick by value, smallest first:

1. **Highest concrete value: a universal *run-tests* verb for the freshly-bridged repos.** shotsmith
   already declares `test_command: pytest -q` in `project.yml`; a universal `/test` skeleton that runs
   the declared command (default `pytest -q`, guarded `if test_command set or tests/ exists`) gives
   shotsmith a real `/test` for free, c3d correctly no-ops (its `command-profile.local.md` already says
   no test runner), devpulse no-ops. **First resolve the `/test` name clash** (run vs generate) — that
   decision gates everything else. If `/test` = run, the iOS pack's test-*generation* content moves to
   a separate verb or stays a pack command; the universal `## /test` (run) goes into
   `packs/python/command-profile.md` (pytest) and `packs/ios/command-profile.md` (xcodebuild test).
   Then **add `test` to `bridge-symlink.sh` `COMMANDS` and to `/conform` Check B's non-iOS set**, and
   `git rm` whatever pack command it supersedes (mirror how Phase A deleted `templates/commands/{status,wrapup}.md`).
2. **`/context-health` → skeleton+profile** only when a kind-specific signal is actually wanted. It's
   already universal+bridged, so this is a low-risk pattern application with no bridge/conform churn —
   a fine warm-up if you want to exercise the mechanics, but it adds little until a signal asks.
3. **`/preflight`** last, and only if you decide it should be universal at all (see above). If it stays
   iOS-pack, that's a legitimate Phase C outcome — record the decision in `COMMANDS-ARCHITECTURE.md`.

Do each as its **own branch + PR** (in `_playbook`; the bridged repos inherit universal-command and
`command-profile.md` changes automatically through their symlinks — that propagation is the whole
point, so verify it in a bridged repo rather than re-editing each).

## Verify (gates — same as Phase A/B)
- **Byte-identical iOS compose** for every artifact a change doesn't intend to touch: run
  `compose-claude.sh <scratch> ios` before/after and diff; only the converted verb + its
  `command-profile.md` section should differ.
- **Lossy-extraction:** the new skeleton + profile section reproduces every step of the command it
  replaces (diff against the `git rm`'d original from git history if unsure).
- **`/conform` clean on both sides:** iOS still expects the full composed set; non-iOS expects the
  (possibly newly-extended) bridged set — update Check B in lockstep with `bridge-symlink.sh`.
- **Real run in a bridged repo:** if you ship a universal run-`/test`, confirm shotsmith's symlinked
  `/test` actually runs `pytest -q` and c3d/devpulse no-op cleanly.

## Constraints (invariants — do not violate)
- Never push `main`; one branch + PR per logical conversion; commit with **explicit pathspecs**
  (never stage `_playbook`'s dirty `inbox.md`; `git check-ignore` before each commit — `.claude/*` has
  bitten this repo before).
- Keep changes **downstream-aware:** edits under `.claude/commands/`, `packs/*/commands/`, and
  `packs/*/command-profile.md` are downstream-visible → add a `CHANGELOG.md` entry per the playbook's
  own `command-profile.local.md` `/wrapup` discipline. Internal docs (this file, root `CLAUDE.md`,
  `COMMANDS-ARCHITECTURE.md`, `REFACTOR-PLAN.md`) are **not** distributed → no CHANGELOG entry.
- Keep `REFACTOR-PLAN.md` (the context-loss anchor) and `COMMANDS-ARCHITECTURE.md` current as
  decisions land — that's how this initiative kills drift.

## Related stream (not Phase C work)
The immediate **rules pass** — make `core/rules/git-workflow.md` truly core — has its own
`RULES-PASS-HANDOFF.md` and runs *before* this phase; don't fold it into Phase C command work. Once
it lands, drop this note.

Remaining watch-for that is Phase-C-adjacent:
- **Add a `packs/<pack>/rules` loop to `bridge-symlink.sh`** when a non-iOS pack first gains a
  `rules/` dir (today `packs/python` + `packs/cli` are command-profile-only; the bridge links only
  `core/rules`; `compose-claude.sh` already composes core + pack rules for iOS). A comment in the
  script marks the spot.

## Out of scope (don't start unprompted — each tracked in REFACTOR-PLAN)
Stage 1b (graduate the iOS apps to the Claude marketplace + re-pin submodules); Stage 2 (vendor the
SHA-pinned Hudson fork — beyond *referencing* it for `/test`); Stage 3 (port the dynamic verbs to MCP
tools reading `project.yml`); iCloud rollback-copy deletion (HELD); PlaybookLauncher spin-out (Stage
4); the broadsheet Fastfile → Shotsmith migration.
