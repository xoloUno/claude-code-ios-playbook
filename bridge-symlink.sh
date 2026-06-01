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
set -euo pipefail

# Link sources come from THIS script's own playbook tree; <playbook> in the links is its
# basename, so a renamed playbook dir still links correctly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYBOOK_NAME="$(basename "$SCRIPT_DIR")"

TARGET="${1:?usage: bridge-symlink.sh <target-dir> [pack]}"
PACK="${2:-}"

# The universal commands bridged to every non-iOS repo — exactly these five verbs.
# Deliberately excluded: capture-manual-surfaces (iOS-only), upgrade (moot for always-current
# live symlinks), curate (playbook-only). playbook-inbox is a *rule* (linked below as-is) so
# its live $PLAYBOOK_HOME token resolves at read time — no compose-time substitution here.
COMMANDS=(status wrapup conform context-health inbox)

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

mkdir -p "$TARGET/.claude/rules" "$TARGET/.claude/commands"

# --- core rules (the universal rules; glob so a newly-added core rule is bridged too) -------
rules_linked=0
for src in "$SCRIPT_DIR"/core/rules/*.md; do
  [[ -e "$src" ]] || continue
  name="$(basename "$src")"
  if relink "$TARGET/.claude/rules/$name" "../../../$PLAYBOOK_NAME/core/rules/$name"; then
    rules_linked=$((rules_linked + 1))
  fi
done

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

echo "✓ bridged $TARGET/.claude → $PLAYBOOK_NAME ($rules_linked core rules + $cmds_linked commands$profile_note)"
