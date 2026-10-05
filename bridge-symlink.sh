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
# The sibling layout is checked before anything changes. After that, any failure (a link that
# can't be created or dangles, a failed render) is reported as a possibly partial update; the
# script never tries to restore anything.
#
# AGENTS.md opt-in: a repo whose AGENTS.md carries the playbook core markers gets the core
# block rendered into AGENTS.md (by compose-agents-md.py) instead of core-rule symlinks. Rules
# linked from outside the repo didn't load on current Claude Code without an external-import
# approval, while AGENTS.md (with CLAUDE.md as its relative symlink) loaded from the repo root
# and from subdirectories. In that mode the script validates the layout before changing
# anything, links commands and the profile as before, renders the block, and only then removes
# its own known core-rule links (never real files or other symlinks). The block is a rendered
# copy: re-run this script to refresh it. The script prints the playbook revision it used,
# marked "+uncommitted" when the playbook source has uncommitted edits.
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

# partial <reason> — the single failure path once changes have begun. It reports and exits;
# it never tries to restore anything.
partial() {
  echo "✗ bridge stopped after it began changing $TARGET: $1." >&2
  echo "  Links under .claude/ (and AGENTS.md, for an opted-in repo) may be partially updated; review the target before retrying." >&2
  exit 1
}

# relink <link-path> <relative-target>
#   returns 0 = linked, 1 = skipped (a real file is there). Failing to create or re-point the
#   link, or a link that dangles, goes through partial().
relink() {
  local link="$1" rel="$2"
  if [[ -L "$link" ]]; then
    ln -snf "$rel" "$link" || partial "could not re-point $link"   # idempotent re-point
  elif [[ -e "$link" ]]; then
    echo "  ⚠ skip (real file, not a symlink): $link" >&2
    echo "    git rm it first if you mean to replace it with the shared one." >&2
    return 1
  else
    ln -s "$rel" "$link" || partial "could not create $link"
  fi
  [[ -e "$link" ]] || partial "dangling link $link -> $rel"      # -e follows the link
  return 0
}

# --- Preflight (nothing changes until every check passes) -----------------------------------
fail() { echo "✗ $1. Nothing was changed." >&2; exit 2; }
# The relative links assume the repo and this playbook share a parent directory (~/dev).
target_parent="$(cd "$TARGET/.." 2>/dev/null && pwd -P)" || fail "can't resolve the parent of $TARGET"
[[ "$target_parent/$PLAYBOOK_NAME" -ef "$SCRIPT_DIR" ]] \
  || fail "$TARGET isn't a sibling of this playbook ($target_parent/$PLAYBOOK_NAME is not $SCRIPT_DIR)"

AGENTS_MODE=legacy
if [[ -f "$TARGET/AGENTS.md" ]] && grep -q 'playbook:core:' "$TARGET/AGENTS.md"; then
  command -v python3 >/dev/null || fail "python3 is required for an opted-in AGENTS.md"
  [[ -f "$SCRIPT_DIR/compose-agents-md.py" ]] || fail "the generator is missing: $SCRIPT_DIR/compose-agents-md.py"
  python3 "$SCRIPT_DIR/compose-agents-md.py" check "$TARGET" "$SCRIPT_DIR" >/dev/null
  AGENTS_MODE=opted-in
fi

# Record which playbook revision the links and block come from, flagging uncommitted source edits.
SOURCE_REV="$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"
if [[ "$SOURCE_REV" != unknown && -n "$(git -C "$SCRIPT_DIR" status --porcelain -- \
      core .claude/commands packs compose-agents-md.py bridge-symlink.sh 2>/dev/null)" ]]; then
  SOURCE_REV="$SOURCE_REV+uncommitted"
fi

trap 'partial "a command failed"' ERR

mkdir -p "$TARGET/.claude/rules" "$TARGET/.claude/commands"

# --- core rules: legacy repos only; opted-in repos get the block instead ---------------------
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

# --- universal commands (exactly the ones in COMMANDS) ---------------------------------------
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

# --- opted-in: render the block, then drop only this script's own core-rule links ------------
# The links go last, after the block is in place, so a failure never leaves the repo with
# neither the links nor the block.
if [[ "$AGENTS_MODE" == opted-in ]]; then
  python3 "$SCRIPT_DIR/compose-agents-md.py" write "$TARGET" "$SCRIPT_DIR" \
    || partial "could not render the core block into AGENTS.md"
  core_links_removed=0
  for src in "$SCRIPT_DIR"/core/rules/*.md; do
    [[ -e "$src" ]] || continue
    name="$(basename "$src")"
    link="$TARGET/.claude/rules/$name"
    if [[ -L "$link" && "$(readlink "$link")" == "../../../$PLAYBOOK_NAME/core/rules/$name" ]]; then
      rm "$link" || partial "could not remove $link"
      core_links_removed=$((core_links_removed + 1))
    elif [[ -e "$link" || -L "$link" ]]; then
      echo "  ⚠ keeping $link: it isn't this script's core-rule link. Review it;" >&2
      echo "    /conform reports it as DUPLICATE_CORE while it loads alongside the block." >&2
    fi
  done
  echo "✓ bridged $TARGET/.claude → $PLAYBOOK_NAME @ $SOURCE_REV (core in AGENTS.md; $core_links_removed core-rule links removed; $cmds_linked commands$profile_note)"
else
  echo "✓ bridged $TARGET/.claude → $PLAYBOOK_NAME @ $SOURCE_REV ($rules_linked core rules + $cmds_linked commands$profile_note)"
fi
