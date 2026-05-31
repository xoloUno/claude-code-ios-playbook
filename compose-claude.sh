#!/usr/bin/env bash
# compose-claude.sh — assemble a project's .claude/rules + .claude/commands from the
# playbook's core/ + a platform pack, applying the same substitutions bootstrap.sh does.
#
# Two callers share this one compose path so they can't drift:
#   • bootstrap.sh  — scaffolding a brand-new project
#   • the submodule bridge — an existing iOS app refreshing .claude/ from the pinned
#     _playbook submodule (Stage 1a). Run after `git submodule update`.
#
# Usage:  compose-claude.sh <target-dir> [pack] [primary-sim]
#   target-dir   project root to write .claude/ into            (required)
#   pack         platform pack under packs/<pack>/              (default: ios)
#   primary-sim  value for the __PRIMARY_SIM__ marker / sim swap (default: iPhone 17 Pro)
#
# Source location: $PLAYBOOK_HOME if set, else this script's own directory (so the
# submodule copy self-locates without any env). macOS `sed -i ''` — run locally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYBOOK_DIR="${PLAYBOOK_HOME:-$SCRIPT_DIR}"

TARGET="${1:?usage: compose-claude.sh <target-dir> [pack] [primary-sim]}"
PACK="${2:-ios}"
PRIMARY_SIM="${3:-iPhone 17 Pro}"

mkdir -p "$TARGET/.claude/commands" "$TARGET/.claude/rules"

# --- Commands ---------------------------------------------------------------
# Pack commands (platform-specific) + universal/playbook commands (curate is
# playbook-only) + downstream-only template variants (currently /status, /wrapup).
cmds_copied=0
for cmd in "$PLAYBOOK_DIR/packs/$PACK/commands"/*.md; do
  [[ -e "$cmd" ]] || continue
  cp "$cmd" "$TARGET/.claude/commands/"
  cmds_copied=$((cmds_copied + 1))
done
if [[ -d "$PLAYBOOK_DIR/.claude/commands" ]]; then
  for cmd in "$PLAYBOOK_DIR/.claude/commands"/*.md; do
    cmd_name=$(basename "$cmd")
    [[ "$cmd_name" == "curate.md" ]] && continue  # playbook-only command
    cp "$cmd" "$TARGET/.claude/commands/$cmd_name"
  done
fi
if [[ -d "$PLAYBOOK_DIR/.claude/templates/commands" ]]; then
  for cmd in "$PLAYBOOK_DIR/.claude/templates/commands"/*.md; do
    cmd_name=$(basename "$cmd")
    cp "$cmd" "$TARGET/.claude/commands/$cmd_name"
  done
fi

# --- Rules ------------------------------------------------------------------
# core/ (universal) + packs/<pack>/ (platform).
rules_copied=0
for src in "$PLAYBOOK_DIR/core/rules" "$PLAYBOOK_DIR/packs/$PACK/rules"; do
  [[ -d "$src" ]] || continue
  for rule in "$src"/*.md; do
    [[ -e "$rule" ]] || continue
    cp "$rule" "$TARGET/.claude/rules/"
    rules_copied=$((rules_copied + 1))
  done
done

# --- Substitutions ----------------------------------------------------------
# Inbox rule learns where the playbook lives so sessions know where to capture.
if [[ -f "$TARGET/.claude/rules/playbook-inbox.md" ]]; then
  sed -i '' "s|PLAYBOOK_PATH|$PLAYBOOK_DIR|g" "$TARGET/.claude/rules/playbook-inbox.md"
fi
# preflight uses a __PRIMARY_SIM__ marker — always fill it (even with the default).
if [[ -f "$TARGET/.claude/commands/preflight.md" ]]; then
  sed -i '' "s|__PRIMARY_SIM__|${PRIMARY_SIM}|g" "$TARGET/.claude/commands/preflight.md"
fi
# build-deploy/testing carry the literal default sim — only swap when overridden.
if [[ "${PRIMARY_SIM}" != "iPhone 17 Pro" ]]; then
  for f in "$TARGET/.claude/rules/build-deploy.md" "$TARGET/.claude/rules/testing.md"; do
    [[ -f "$f" ]] && sed -i '' "s|iPhone 17 Pro|${PRIMARY_SIM}|g" "$f"
  done
fi

echo "✓ .claude composed from playbook ($cmds_copied $PACK-pack commands + universal; $rules_copied rules: core + $PACK)"
