# Rules pass — make `core/rules/git-workflow.md` truly core

> **This is the immediate next session** (per `REFACTOR-PLAN.md` §9), *before* the Phase C
> command-generalization in `PHASE-C-HANDOFF.md`. Narrow, concrete, and already-painful: Phase B's
> symlink bridge now distributes an iOS-tainted **core** rule into the non-iOS repos, so non-iOS
> sessions are reading git guidance that doesn't apply to them. Clean that up first.

**Run from `~/dev/_playbook`. Use sibling repos under `~/dev` only for read-only verification**
(the rule lives in `_playbook`; iOS repos get it via `compose-claude.sh`, non-iOS repos via the live
symlink — both update from this one source). Read `~/dev/_playbook/CLAUDE.md` first (prime directive:
kill drift; never push `main`; explicit pathspecs — never stage the dirty `inbox.md`).

## The problem
`core/rules/git-workflow.md` is a **core** rule — composed into every iOS repo *and*, since Phase B,
symlinked into every non-iOS repo (devpulse, shotsmith, c3d). But it still welds iOS/App-Store
knowledge into that universal file — the exact disease Phase A fixed for commands (kind knowledge in
a universal file → everyone forks/inherits the wrong thing). The bridge just widened the leak. Make
the core rule truly universal; the iOS specifics move to (or already live in) the iOS pack.

## Orient (read first)
- `~/dev/_playbook/CLAUDE.md` — operating guide + invariants; `COMMANDS-ARCHITECTURE.md` **"Related
  cleanup"** (this *is* the tracked item) and the core-vs-pack carve model; `REFACTOR-PLAN.md` §9
  (this is "the rules pass").
- **Precedent:** the Phase A carve (commit `0113986`) split rules into `core/rules` + `packs/ios/rules`.
- **Key — the overlap that makes this mostly deletion:** `packs/ios/command-profile.md` `## /wrapup`
  **already owns** the iOS session-end commit behavior (`[skip ci]` local/cloud, `release-notes-draft`,
  prose-humanizer, scope items), and the universal `_playbook/.claude/commands/wrapup.md` already owns
  the generic flow (branch route → mutations → gates → stage → commit → push). So the canonical home
  for "what to do at commit time" is now the **`/wrapup` command + its kind profile**, not this rule.
  Much of git-workflow.md's "Claude Code Commit Behavior" section is now redundant.

## Current state (verified 2026-06-01 — re-verify before acting)
`core/rules/git-workflow.md`, with the iOS-isms by line:
- **L3 frontmatter** `globs: **/*.swift, **/*.yml, **/project.yml` — Swift-scoped; a *core* rule
  should match broadly (`**/*`), not just Swift repos.
- **L14** `dev ← active development` branch strategy — the non-iOS repos use `main` + feature branches
  (no `dev`); the universal `/wrapup` already routes branches generically. Present `dev` as optional,
  not the assumed model.
- **L29** commit type `ui` — iOS-UI-specific; drop from the core list (or note it as pack-added).
- **L39–40** `[skip ci]` local vs cloud — **already in** `packs/ios/command-profile.md` `## /wrapup`;
  the universal `wrapup.md` explicitly says `[skip ci]` is kind-specific (from the profile). Remove
  from the core rule.
- **L42** mandatory "Update **Current State** in CLAUDE.md" — the universal `/status`+`/wrapup` guard
  CLAUDE.md "Current State" with *if present* (c3d uses "Current Phase"; shotsmith has no CLAUDE.md;
  the playbook's CLAUDE.md is principles-only). Not universal; not mandatory.
- **L43** "Update `WORKLOG.md`" — `work-log.md` is a core rule, but the universal `/wrapup` treats
  WORKLOG as *only if present*; the **mandatory** framing here is the iOS-app assumption to drop.
- **L44** "Update `release-notes-draft.md`" — App-Store concept; **already in**
  `packs/ios/command-profile.md`. Remove from the core rule.
- **L57** `git tag … "App Store v1 submission"` — iOS example; genericize.

`packs/ios/rules/` already has 10 iOS rules (asc-troubleshooting, build-deploy, code-style, …) but
**no** git rule — because the iOS git behavior is in the command profile, not a rule. So you likely
do **not** need a new `packs/ios/rules/git-workflow.md`; verify the behavior is fully covered by
`packs/ios/command-profile.md` before adding anything.

## The fix (recommended; apply judgment per line)
1. **`core/rules/git-workflow.md` → truly universal:**
   - frontmatter `globs` → `**/*` (broad), description unchanged.
   - **Branch strategy:** generalize to `main` + `feature/*` / `fix/*`; mention `dev` as an *optional*
     integration branch, not the assumed one. Keep "never commit directly to `main`" and the
     worktree note (both universal).
   - **Commit convention:** keep the universal types (`feat`/`fix`/`refactor`/`chore`/`docs`/`test`);
     drop `ui` (or mark it pack-added). Keep the ≤72-char / present-tense / `Co-Authored-By` mechanics.
   - **"Claude Code Commit Behavior":** trim to the universal mechanics (review `git status`, stage
     selectively, conventional commit + `Co-Authored-By`, push to a branch not `main`) and **defer the
     session-end record-mutations to `/wrapup`** — delete the `[skip ci]`, "Current State", WORKLOG,
     and release-notes bullets (they're iOS specifics already owned by the command + iOS profile).
     Consider replacing them with a one-line pointer: "session-end record steps are driven by
     `/wrapup` + the project's `command-profile`."
   - **Tagging:** genericize the example message (drop "App Store v1 submission").
2. **iOS residue:** for anything iOS-specific *not* already covered by `packs/ios/command-profile.md`,
   add it to the iOS pack (prefer the existing command profile over a new rule). Expect this to be
   little-to-nothing given the Phase A overlap — check before creating a file.
3. **Confirm no iOS behavior is lost:** every iOS bullet you remove from the core rule must still be
   reachable for an iOS app via `packs/ios/command-profile.md` + the universal `/wrapup`. (Phase A's
   audit says it is — verify, don't assume.)

## Verify (gates)
- **This is NOT a byte-identical-compose change** — the rule content changes by design. The gate is
  **net-behavior-preserving for iOS + kind-clean for non-iOS:**
  - **iOS:** `compose-claude.sh <scratch> ios` then read the composed `.claude/rules/git-workflow.md`
    + `.claude/command-profile.md`: together they must still carry every git behavior an iOS app had
    (no `[skip ci]`/Current-State/release-notes capability lost — just relocated to the profile).
  - **non-iOS:** `cat` the symlinked `git-workflow.md` in shotsmith/devpulse/c3d (auto-updated via the
    live symlink) — confirm it no longer contains Swift globs, `dev`-only strategy, `[skip ci]`,
    mandatory "Current State", or App-Store tagging.
- **`/conform` clean:** Check A diffs each project's `git-workflow.md` against `core/rules/`; the
  symlink *is* the source and the iOS composed copy is the same de-iOS'd core rule, so both match.

## Watch-for (the second tracked follow-up — only if it comes up)
If this pass ends up creating a **non-iOS** pack rule (`packs/python/rules/…` or `packs/cli/rules/…`
— e.g. a python-specific git nuance), then also **add the `packs/<pack>/rules` loop to
`bridge-symlink.sh`** (a comment in the script marks the exact spot; `compose-claude.sh` already does
core + pack rules for iOS). Today no non-iOS pack has a `rules/` dir, so the bridge change stays
latent — do it only if you create such a rule, and update `/conform` Check A's pack-rules audit to
match.

## Constraints / wrap
- Never push `main`; one branch + PR; explicit pathspecs (never stage `inbox.md`; `git check-ignore`
  before committing).
- **CHANGELOG entry required:** `core/rules/*` is composed + symlinked downstream → downstream-visible
  per the playbook's own `command-profile.local.md` `/wrapup` rule. If it retracts earlier guidance,
  add a `Superseded by:` banner per the CHANGELOG convention.
- Keep `REFACTOR-PLAN.md` §9 + `COMMANDS-ARCHITECTURE.md` "Related cleanup" current — mark this done
  when it lands, and that unblocks `PHASE-C-HANDOFF.md`.

## Out of scope
Phase C command-generalization (`PHASE-C-HANDOFF.md`) — comes *after* this. Auditing the other core
rules for leaks beyond `git-workflow.md` (note any you spot, but don't expand this pass unless Erik
asks). Stage 1b / Stage 2 (Hudson) / Stage 3 (MCP) / iCloud deletion / PlaybookLauncher.
