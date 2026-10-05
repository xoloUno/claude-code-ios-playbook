#!/usr/bin/env bash
# resolve-xcode-scheme.sh — print the shell-ready -scheme argument for an iOS project, or
# nothing if it can't be resolved.
#
# Usage:  resolve-xcode-scheme.sh <project-dir>
#
# Precedence:
#   1. XCODE_SCHEME from the environment. Composing callers load the project's .env.project
#      into the environment first (set -a; . ./.env.project; set +a).
#   2. project.yml's first top-level `name:`, if it's one of the supported YAML scalars:
#        name: Plain Name            # a trailing comment after whitespace is dropped
#        name: "Double Quoted"       # no backslash escapes
#        name: 'Single Quoted'       # '' stands for one '
#      Empty, comment-only, and any other form (anchors, aliases, tags, flow or block
#      scalars, escapes) count as unresolved.
#
# Output is one shell word: the bare name when it's only [A-Za-z0-9._+-], otherwise the name
# single-quoted with any ' written as '\''. compose-claude.sh and /conform both use this
# script, so the substitution can't drift between them. Exit status is always 0; empty output
# means unresolved.
set -euo pipefail

TARGET="${1:?usage: resolve-xcode-scheme.sh <project-dir>}"
scheme="${XCODE_SCHEME:-}"

if [[ -z "$scheme" && -f "$TARGET/project.yml" ]]; then
  line="$(grep -m1 '^name:' "$TARGET/project.yml" || true)"
  val="${line#name:}"
  val="${val%$'\r'}"
  val="${val#"${val%%[![:space:]]*}"}"                 # trim leading whitespace
  re_dq='^"([^"\\]*)"[[:space:]]*(#.*)?$'
  re_sq="^'(([^']|'')*)'[[:space:]]*(#.*)?$"
  if [[ "$val" =~ $re_dq ]]; then
    scheme="${BASH_REMATCH[1]}"
  elif [[ "$val" =~ $re_sq ]]; then
    m=${BASH_REMATCH[1]}
    scheme=${m//"''"/"'"}
  elif [[ -n "$val" && "$val" != [\#\"\'\&\*\!\|\>\%\@\`\{\[]* ]]; then
    val="${val%%[[:space:]]#*}"                       # drop a trailing " # comment"
    scheme="${val%"${val##*[![:space:]]}"}"           # trim trailing whitespace
  fi
fi

[[ -n "$scheme" ]] || exit 0
if [[ "$scheme" =~ ^[A-Za-z0-9._+-]+$ ]]; then
  printf '%s\n' "$scheme"
else
  q="'\''"                                           # the 4 characters '\''
  escaped=${scheme//"'"/$q}
  printf "'%s'\n" "$escaped"
fi
