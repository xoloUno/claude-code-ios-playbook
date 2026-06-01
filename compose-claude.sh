#!/usr/bin/env bash
# compose-claude.sh — assemble a project's .claude/rules, .claude/commands, and the kind
# command-profile.md from the playbook's core/ + a platform pack, applying the same
# substitutions bootstrap.sh does.
#
# Two callers share this one compose path so they can't drift:
#   • bootstrap.sh  — scaffolding a brand-new project
#   • the submodule bridge — an existing iOS app refreshing .claude/ from the pinned
#     _playbook submodule (Stage 1a). Run after `git submodule update`.
#
# Usage:  compose-claude.sh <target-dir> [pack]
#   target-dir   project root to write .claude/ into   (required)
#   pack         platform pack under packs/<pack>/      (default: ios)
#
# Per-project values come from the environment (export them, or `set -a; source
# .env.project; set +a` first), each with a generic default so an unconfigured project
# still composes cleanly:
#   PRIMARY_SIM            build/test simulator           (default: iPhone 17 Pro)
#   PROVISIONING_PROFILES  ASC profile names for deploy   (default: see the Fastfile)
#   METADATA_LOCALES       metadata locale dirs to check  (default: en-US)
#
# Sources load from this script's own tree (the submodule self-locates with no env). The
# inbox path resolves to $PLAYBOOK_HOME (the central playbook, from ~/.config/playbook/config)
# so captured lessons aggregate there, never in a per-app submodule checkout.
# macOS `sed -i ''` — run locally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Sources come from THIS script's own playbook tree — the submodule when the bridge runs it,
# the central playbook when bootstrap calls it through its resolved path.
PLAYBOOK_DIR="$SCRIPT_DIR"
# Inbox lives in the canonical playbook home so lessons land centrally, not per-app.
PLAYBOOK_INBOX="${PLAYBOOK_HOME:-$SCRIPT_DIR}"

TARGET="${1:?usage: compose-claude.sh <target-dir> [pack]}"
PACK="${2:-ios}"
PRIMARY_SIM="${PRIMARY_SIM:-iPhone 17 Pro}"
PROVISIONING_PROFILES="${PROVISIONING_PROFILES:-see the Fastfile}"
METADATA_LOCALES="${METADATA_LOCALES:-en-US}"

mkdir -p "$TARGET/.claude/commands" "$TARGET/.claude/rules"

# --- Commands ---------------------------------------------------------------
# Pack commands (platform-specific) + universal commands (curate is playbook-only).
# /status and /wrapup are universal skeletons living in .claude/commands/; they load the
# kind layer (command-profile.md, copied below) and any project-owned profile at runtime.
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

# --- Command profile (kind layer) -------------------------------------------
# The pack's command-profile.md carries the type-level /status + /wrapup behavior the
# universal skeletons fold in at runtime. Lives at .claude/ root (not a slash command,
# not scanned by /conform Check F). A project's own command-profile.local.md is
# project-owned and never composed.
if [[ -f "$PLAYBOOK_DIR/packs/$PACK/command-profile.md" ]]; then
  cp "$PLAYBOOK_DIR/packs/$PACK/command-profile.md" "$TARGET/.claude/command-profile.md"
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
# Inbox rule learns where the playbook lives so sessions know where to capture. The rule
# carries the literal token $PLAYBOOK_HOME (resolved live when read in a symlinked repo);
# composed copies bake the real absolute path here so they stay self-contained.
if [[ -f "$TARGET/.claude/rules/playbook-inbox.md" ]]; then
  sed -i '' "s|[$]PLAYBOOK_HOME|$PLAYBOOK_INBOX|g" "$TARGET/.claude/rules/playbook-inbox.md"
fi
# Per-project markers in command files: scalars with generic defaults, like __PRIMARY_SIM__.
# Each app fills these from its .env.project; unset → the generic default above.
for f in "$TARGET/.claude/commands"/*.md; do
  [[ -e "$f" ]] || continue
  sed -i '' \
    -e "s|__PRIMARY_SIM__|${PRIMARY_SIM}|g" \
    -e "s|__PROVISIONING_PROFILES__|${PROVISIONING_PROFILES}|g" \
    -e "s|__METADATA_LOCALES__|${METADATA_LOCALES}|g" \
    "$f"
done
# build-deploy/testing carry the literal default sim — only swap when overridden.
if [[ "${PRIMARY_SIM}" != "iPhone 17 Pro" ]]; then
  for f in "$TARGET/.claude/rules/build-deploy.md" "$TARGET/.claude/rules/testing.md"; do
    [[ -f "$f" ]] && sed -i '' "s|iPhone 17 Pro|${PRIMARY_SIM}|g" "$f"
  done
fi

profile_note=""
[[ -f "$TARGET/.claude/command-profile.md" ]] && profile_note="; $PACK command-profile"
echo "✓ .claude composed from playbook ($cmds_copied $PACK-pack commands + universal; $rules_copied rules: core + $PACK$profile_note)"
