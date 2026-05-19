#!/usr/bin/env bash
# Legacy PreToolUse hook: enforce_codex_exec.sh
# Retained for compatibility with earlier Claude-wrapped playbook installs.
# This project is Codex-only, so this guard is disabled by default.
# Direct edits by the current Codex session are allowed; nested Codex subprocesses
# are not part of the active workflow.
#
# Configuration:
#   PLAYBOOK_CODE_PATH_PREFIXES  colon-separated relative path prefixes treated as
#                                application code. Default: app/:src/:lib/:tests/
#   PLAYBOOK_CODEX_ENFORCEMENT   set to "legacy-claude" to enable this guard

set -euo pipefail

if [ "${PLAYBOOK_CODEX_ENFORCEMENT:-off}" != "legacy-claude" ]; then
  exit 0
fi

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

PREFIXES="${PLAYBOOK_CODE_PATH_PREFIXES:-app/:src/:lib/:tests/}"
IFS=':' read -ra PATHS <<< "$PREFIXES"

for PREFIX in "${PATHS[@]}"; do
  if [ -z "$PREFIX" ]; then
    continue
  fi

  if [[ "$FILE_PATH" == "$PREFIX"* ]] || [[ "$FILE_PATH" == *"/${PREFIX}"* ]]; then
    echo "BLOCKED: legacy wrapped edits to application code are disabled for '${FILE_PATH}'." >&2
    echo "Use the current Codex session directly and wait for IMPLEMENTATION_RESULT." >&2
    echo "This repository reserves application code writing for Codex-only execution." >&2
    exit 2
  fi
done

exit 0
