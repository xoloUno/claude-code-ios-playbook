#!/usr/bin/env bash
# codex-review.sh <prompt-file> <name> — run one read-only Codex review non-interactively.
#
# A second opinion during development, and the merge review under the core "Autonomy"
# checklist. Run it from the playbook, from inside the repo under review:
#   "$PLAYBOOK_HOME"/tools/codex-review.sh <prompt-file> <name>
# Codex runs under a permissions profile built from the ":workspace" built-in: it writes only
# to a fresh temp workspace, and the OS denies it reads of the personal folders in DENY_READ.
# A repo inside one of them (a project under ~/Documents) stays readable: the script denies
# that folder's other entries instead, because a nested "read" can't override a parent
# "deny" (probed on codex-cli 0.163).
# Its final message lands in /private/tmp/codex-reviews/<name>-<time>/review.md. Findings
# are inputs, not approvals.
#
# Overrides: CODEX_BIN, CODEX_MODEL, CODEX_EFFORT, CODEX_TIER.
set -euo pipefail
CODEX="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex}"
MODEL="${CODEX_MODEL:-gpt-6.1-sol}"
EFFORT="${CODEX_EFFORT:-high}"
TIER="${CODEX_TIER:-priority}"
DENY_READ=("$HOME/Documents" "$HOME/Desktop" "$HOME/Downloads" "$HOME/Library/Mobile Documents"
           "$HOME/Library/Mail" "$HOME/Library/Messages" "$HOME/.ssh" "$HOME/.aws")

usage() { echo "usage: codex-review.sh <prompt-file> <name>" >&2; exit 2; }
fail() { echo "✗ $*" >&2; exit 2; }
[[ $# -eq 2 ]] || usage
PROMPT_FILE="$1" NAME="$2"
[[ "$NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]] || fail "name must match [a-z0-9-]+: $NAME"
[[ -f "$PROMPT_FILE" ]] || fail "prompt file not found: $PROMPT_FILE"
[[ -x "$CODEX" ]] || fail "codex CLI not found: $CODEX"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] && REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

deny=""
add_deny() { local p="${1//\\/\\\\}"; p="${p//\"/\\\"}"; deny+="${deny:+, }\"$p\"=\"deny\""; }
for d in "${DENY_READ[@]}"; do
  if [[ -z "$REPO_ROOT" || "$REPO_ROOT/" != "$d/"* ]]; then add_deny "$d"; continue; fi
  while [[ "$d" != "$REPO_ROOT" ]]; do   # deny the siblings at each level down to the repo
    rest="${REPO_ROOT#"$d"/}"
    next="$d/${rest%%/*}"
    while IFS= read -r -d '' e; do [[ "$e" == "$next" ]] || add_deny "$e"; done \
      < <(find "$d" -mindepth 1 -maxdepth 1 -print0)
    d="$next"
  done
done

OUT="/private/tmp/codex-reviews/$NAME-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT/work"
cp "$PROMPT_FILE" "$OUT/prompt.md"

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
