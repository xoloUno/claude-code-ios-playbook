#!/usr/bin/env bash
# bridge-symlink.sh — bridge a non-iOS repo's .claude/ onto the shared playbook source via
# live, relative symlinks. The non-iOS counterpart to the iOS path (pinned submodule +
# compose-claude.sh copies): no compose step, no version pin — the links resolve against the
# sibling playbook working tree, so the repo always runs the current shared rules/commands.
#
# Usage:  bridge-symlink.sh <target-dir> [pack]
#   target-dir   the repo to (re)bridge; its .claude/ is linked. Usually "." run from the repo.
#   pack         optional platform pack under packs/<pack>/. When given AND
#                packs/<pack>/command-profile.md exists, the kind-layer profile is linked too.
#                Omit for a kind-of-one (e.g. c3d): no pack, so no command-profile.md link —
#                its behavior lives in a project-owned command-profile.local.md this script
#                never touches.
#
# Surgical + idempotent by design:
#   • never `rm -rf .claude/`; only `mkdir -p` the two dirs it needs.
#   • (re)links a path only when it is absent or already a symlink — re-running just re-points
#     the links. A REAL file is warned about and skipped, never overwritten: a bespoke command
#     must be `git rm`'d intentionally before the shared one can take its place.
#   • never writes project-owned files: .claude/settings.local.json, .claude/project.yml,
#     .claude/command-profile.local.md.
#
# Relative links (so a moved/renamed ~/dev tree keeps resolving) assume <target> is a sibling
# of the playbook under one parent (~/dev). Depths differ by one level — note the ../ counts:
#   <target>/.claude/rules/<n>.md       -> ../../../<playbook>/core/rules/<n>.md
#   <target>/.claude/commands/<n>.md    -> ../../../<playbook>/.claude/commands/<n>.md
#   <target>/.claude/command-profile.md -> ../../<playbook>/packs/<pack>/command-profile.md
# Each created link is checked to resolve; a dangling link aborts (target not a sibling?).
#
# AGENTS.md opt-in: a repo whose AGENTS.md carries the playbook core markers gets the core
# block rendered into AGENTS.md (by compose-agents-md.py) instead of core-rule symlinks. Rules
# linked from outside the repo didn't load on current Claude Code without an external-import
# approval, while AGENTS.md (with CLAUDE.md as its relative symlink) loaded from the repo root
# and from subdirectories. In that mode the script validates the layout before changing
# anything, removes only its own known core-rule links (never real files or other symlinks),
# and leaves commands and the profile linked as before. The block is a rendered copy: re-run
# this script to refresh it. The script prints the playbook revision it used.
set -euo pipefail

# Link sources come from THIS script's own playbook tree; <playbook> in the links is its
# basename, so a renamed playbook dir still links correctly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYBOOK_NAME="$(basename "$SCRIPT_DIR")"

TARGET="${1:?usage: bridge-symlink.sh <target-dir> [pack]}"
PACK="${2:-}"

# The universal commands bridged to every non-iOS repo — exactly these six verbs.
# Deliberately excluded: capture-manual-surfaces (iOS-only), upgrade (moot for always-current
# live symlinks), curate (playbook-only). playbook-inbox is a *rule* (linked below as-is) so
# its live $PLAYBOOK_HOME token resolves at read time — no compose-time substitution here.
# `test` is the universal run-the-declared-suite verb; it no-ops cleanly in a repo with no
# test_command and no tests (e.g. c3d), so bridging it everywhere is safe.
COMMANDS=(status wrapup conform context-health inbox test)

# relink <link-path> <relative-target>
#   returns 0 = linked, 1 = skipped (a real file is there); a dangling result aborts the script.
relink() {
  local link="$1" rel="$2"
  if [[ -L "$link" ]]; then
    ln -snf "$rel" "$link"            # existing symlink → idempotent re-point
  elif [[ -e "$link" ]]; then
    echo "  ⚠ skip (real file, not a symlink): $link" >&2
    echo "    git rm it first if you mean to replace it with the shared one." >&2
    return 1
  else
    ln -s "$rel" "$link"
  fi
  if [[ ! -e "$link" ]]; then         # -e follows the link: false ⇒ it dangles
    echo "  ✗ dangling link: $link -> $rel" >&2
    echo "    Is this repo a sibling of $PLAYBOOK_NAME under the same parent (~/dev)?" >&2
    exit 1
  fi
  return 0
}

# --- AGENTS.md opt-in (validated before anything changes) ------------------------------------
AGENTS_MODE=legacy
if [[ -f "$TARGET/AGENTS.md" ]] && grep -q 'playbook:core:' "$TARGET/AGENTS.md"; then
  if ! command -v python3 >/dev/null; then
    echo "✗ python3 is required for an opted-in AGENTS.md. Nothing was changed." >&2
    exit 2
  fi
  if [[ ! -f "$SCRIPT_DIR/compose-agents-md.py" ]]; then
    echo "✗ the generator is missing: $SCRIPT_DIR/compose-agents-md.py. Nothing was changed." >&2
    exit 2
  fi
  python3 "$SCRIPT_DIR/compose-agents-md.py" check "$TARGET" "$SCRIPT_DIR" >/dev/null
  AGENTS_MODE=opted-in
fi
SOURCE_REV="$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"

trap 'echo "✗ bridge stopped after it began changing $TARGET. Links under .claude/ (and AGENTS.md, for an opted-in repo) may be partially updated; review the target before retrying." >&2' ERR

mkdir -p "$TARGET/.claude/rules" "$TARGET/.claude/commands"

# --- opted-in: drop only this script's own core-rule links; the block replaces them --------
core_links_removed=0
if [[ "$AGENTS_MODE" == opted-in ]]; then
  for src in "$SCRIPT_DIR"/core/rules/*.md; do
    [[ -e "$src" ]] || continue
    name="$(basename "$src")"
    link="$TARGET/.claude/rules/$name"
    if [[ -L "$link" && "$(readlink "$link")" == "../../../$PLAYBOOK_NAME/core/rules/$name" ]]; then
      rm "$link"
      core_links_removed=$((core_links_removed + 1))
    elif [[ -e "$link" || -L "$link" ]]; then
      echo "  ⚠ keeping $link: it isn't this script's core-rule link. Review it;" >&2
      echo "    /conform reports it as DUPLICATE_CORE while it loads alongside the block." >&2
    fi
  done
fi

# --- core rules (glob so a newly-added core rule is bridged automatically) ------------------
# Links core/rules ONLY. Non-iOS packs ship no rules/ today (packs/python, packs/cli are
# command-profile-only), so there is nothing else to link. When a non-iOS pack first gains a
# packs/<pack>/rules/, add a second loop here that links it when [pack] is given — compose-claude.sh
# already composes core + pack rules for iOS; without the matching loop, bridged repos would
# silently miss the pack's rules.
rules_linked=0
if [[ "$AGENTS_MODE" == legacy ]]; then
  for src in "$SCRIPT_DIR"/core/rules/*.md; do
    [[ -e "$src" ]] || continue
    name="$(basename "$src")"
    if relink "$TARGET/.claude/rules/$name" "../../../$PLAYBOOK_NAME/core/rules/$name"; then
      rules_linked=$((rules_linked + 1))
    fi
  done
fi

# --- universal commands (exactly the five in COMMANDS) --------------------------------------
cmds_linked=0
for name in "${COMMANDS[@]}"; do
  src="$SCRIPT_DIR/.claude/commands/$name.md"
  if [[ ! -e "$src" ]]; then
    echo "  ⚠ source command missing in playbook, skipping: $src" >&2
    continue
  fi
  if relink "$TARGET/.claude/commands/$name.md" "../../../$PLAYBOOK_NAME/.claude/commands/$name.md"; then
    cmds_linked=$((cmds_linked + 1))
  fi
done

# --- kind-layer command profile (only when a pack is named and it ships one) ----------------
profile_note=""
if [[ -n "$PACK" ]]; then
  if [[ -f "$SCRIPT_DIR/packs/$PACK/command-profile.md" ]]; then
    if relink "$TARGET/.claude/command-profile.md" "../../$PLAYBOOK_NAME/packs/$PACK/command-profile.md"; then
      profile_note="; $PACK command-profile"
    fi
  else
    echo "  ⚠ pack '$PACK' ships no command-profile.md — skipping the profile link" >&2
  fi
fi

if [[ "$AGENTS_MODE" == opted-in ]]; then
  python3 "$SCRIPT_DIR/compose-agents-md.py" write "$TARGET" "$SCRIPT_DIR"
  echo "✓ bridged $TARGET/.claude → $PLAYBOOK_NAME @ $SOURCE_REV (core in AGENTS.md; $core_links_removed core-rule links removed; $cmds_linked commands$profile_note)"
else
  echo "✓ bridged $TARGET/.claude → $PLAYBOOK_NAME @ $SOURCE_REV ($rules_linked core rules + $cmds_linked commands$profile_note)"
fi
