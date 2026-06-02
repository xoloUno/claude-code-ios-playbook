Recompose this project's `.claude/` from the installed playbook plugin.

This is the **marketplace** refresh verb — the graduated replacement for the old submodule
`/upgrade`. When a project consumes the playbook as a Claude marketplace plugin (instead of a
pinned `_playbook` submodule), there is no in-repo source tree to compose from. This command
composes from the **installed plugin** at `${CLAUDE_PLUGIN_ROOT}` instead, so a project's
`.claude/commands` + `.claude/rules` + `command-profile.md` are (re)generated from whatever
plugin version is installed.

It is **on-demand by design** — nothing recomposes on session start. The plugin *source* may
auto-update silently (`autoUpdate: true`), but the composed files in your repo only change when
you run this verb and commit the result. `/conform` remains the drift detector.

## Steps

1. **Resolve the playbook source**, first match wins:
   - `${CLAUDE_PLUGIN_ROOT}` — set when this runs as the installed plugin command. The normal path.
   - `$PLAYBOOK_HOME`, or the `PLAYBOOK_HOME` line in `~/.config/playbook/config` — the local dev
     tree fallback (`~/dev/_playbook`). Use this only if `${CLAUDE_PLUGIN_ROOT}` is unset.
   - If neither resolves to a directory containing `compose-claude.sh`, stop and tell the user
     the plugin doesn't appear to be installed.

2. **Resolve the pack.** Read `.claude/project.yml` `kind` if present; otherwise default to `ios`.
   (compose itself defaults to `ios` when given no pack.)

3. **Recompose.** From the repo root, load any project markers and run the engine:
   ```bash
   set -a; source "${CLAUDE_PROJECT_DIR:-$PWD}/.env.project" 2>/dev/null; set +a
   bash "<resolved-source>/compose-claude.sh" "${CLAUDE_PROJECT_DIR:-$PWD}" "<pack>"
   ```
   `.env.project` supplies the per-project scalars compose substitutes (`PRIMARY_SIM`,
   `PROVISIONING_PROFILES`, `METADATA_LOCALES`); each has a generic default if unset. compose
   self-locates its sources (`core/`, `packs/`) from its own directory, so it reads the plugin's
   bundled tree, not the project.

4. **Review, don't auto-commit.** Show `git -C "${CLAUDE_PROJECT_DIR:-$PWD}" status --short .claude`
   and `git diff -- .claude`. Summarize what changed (commands added/updated, rules refreshed,
   `command-profile.md` written). Composed `.claude/**` is committed and playbook-owned — never
   touch project-owned files (`settings.local.json`, `project.yml`, `command-profile.local.md`,
   `.env.project`). Then ask the user to review and commit; do not stage or commit on their behalf
   unless they ask.

## Notes

- **Idempotent.** Re-running on an unchanged plugin version produces byte-identical output and
  therefore no git diff — running it is always safe.
- **No `.playbook-version`.** The installed plugin's semver is the version of record now; this
  command does not read or write `.playbook-version`.
- **Not the submodule flow.** The legacy `/upgrade` walked the CHANGELOG and bumped a submodule
  pin. This one ignores both — it just (re)composes from the installed plugin.
