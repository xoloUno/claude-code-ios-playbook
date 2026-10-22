#!/usr/bin/env bash
# codex-review.sh <prompt-file> <name> — run one read-only Codex review non-interactively.
#
# Installed by tools/install-autonomy.py to ~/.config/playbook/tools/, and run from there as
#   ~/.config/playbook/tools/codex-review.sh <prompt-file> <name>
# That exact path is the one command the playbook's Claude Code settings exempt from the
# sandbox, so the script guards itself:
#   - <name> must match [a-z0-9-]+, and <prompt-file> must be a regular file inside the
#     current git repo or a temp directory.
#   - Codex runs under a permissions profile built from the ":workspace" built-in: it writes
#     only to a fresh temp workspace, and the OS denies it reads of the personal folders in
#     DENY_READ (verified with a hidden-path probe on codex-cli 0.163).
# Its final message lands in /private/tmp/codex-reviews/<name>-<time>/review.md; the caller
# appends it verbatim to the review log. Verdicts are inputs, not approvals.
#
# Overrides: CODEX_BIN, CODEX_MODEL, CODEX_EFFORT, CODEX_TIER.
set -euo pipefail
CODEX="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex}"
MODEL="${CODEX_MODEL:-gpt-6.1-sol}"
EFFORT="${CODEX_EFFORT:-high}"
TIER="${CODEX_TIER:-priority}"
DENY_READ=("~/Documents" "~/Desktop" "~/Downloads" "~/Library/Mobile Documents"
           "~/Library/Mail" "~/Library/Messages" "~/.ssh" "~/.aws")

usage() { echo "usage: codex-review.sh <prompt-file> <name>" >&2; exit 2; }
fail() { echo "✗ $*" >&2; exit 2; }
[[ $# -eq 2 ]] || usage
PROMPT_FILE="$1" NAME="$2"
[[ "$NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]] || fail "name must match [a-z0-9-]+: $NAME"
[[ -f "$PROMPT_FILE" && ! -L "$PROMPT_FILE" ]] || fail "prompt file must be a regular file: $PROMPT_FILE"
PROMPT_REAL="$(cd "$(dirname "$PROMPT_FILE")" && pwd -P)/$(basename "$PROMPT_FILE")"
ALLOWED=(/private/tmp /tmp /private/var/folders)
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] && ALLOWED+=("$(cd "$REPO_ROOT" && pwd -P)")
ok=0
for root in "${ALLOWED[@]}"; do [[ "$PROMPT_REAL" == "$root"/* ]] && ok=1; done
[[ $ok -eq 1 ]] || fail "prompt file must be inside the current git repo or a temp directory"
[[ -x "$CODEX" ]] || fail "codex CLI not found: $CODEX"

deny=""
for p in "${DENY_READ[@]}"; do deny+="${deny:+, }\"$p\"=\"deny\""; done

OUT="/private/tmp/codex-reviews/$NAME-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT/work"
cp "$PROMPT_REAL" "$OUT/prompt.md"

echo "codex: $("$CODEX" --version) | out: $OUT"
start=$(date +%s)
set +e
"$CODEX" exec \
  -m "$MODEL" -c "model_reasoning_effort=$EFFORT" -c "service_tier=$TIER" \
  -c 'default_permissions="playbook-review"' \
  -c 'permissions.playbook-review.extends=":workspace"' \
  -c "permissions.playbook-review.filesystem={$deny}" \
  -C "$OUT/work" --skip-git-repo-check \
  --json -o "$OUT/review.md" \
  - < "$OUT/prompt.md" > "$OUT/run.jsonl" 2> "$OUT/stderr.txt"
rc=$?
set -e
secs=$(( $(date +%s) - start ))

python3 - "$OUT/run.jsonl" "$rc" "$secs" <<'EOF'
import json, sys
path, rc, secs = sys.argv[1], sys.argv[2], sys.argv[3]
tools = 0; usage = {}; thread = "?"; failed = None
for line in open(path):
    try: o = json.loads(line)
    except Exception: continue
    t = o.get("type")
    if t == "thread.started": thread = o.get("thread_id", "?")
    if t == "turn.completed": usage = o.get("usage", {})
    if t in ("turn.failed", "error"): failed = json.dumps(o)[:300]
    if t == "item.completed" and o.get("item", {}).get("type") in ("command_execution", "mcp_tool_call", "file_change"):
        tools += 1
print(f"exit={rc} secs={secs} thread={thread} tool_items={tools} "
      f"in={usage.get('input_tokens')} out={usage.get('output_tokens')} reasoning={usage.get('reasoning_output_tokens')}")
if failed: print("FAILED:", failed)
EOF
[[ -s "$OUT/review.md" ]] && echo "review: $OUT/review.md" || { echo "✗ no review text; see $OUT/stderr.txt" >&2; exit 1; }
