#!/usr/bin/env bash
# Quick health check for local dev stacks. Usage:
#   AGENT=cursor_sdk bash scripts/check-dev-stack.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="${AGENT:-cursor_sdk}"
API="${NOTION3D_API_BASE:-http://127.0.0.1:8000}"
WEB="${NOTION3D_WEB_BASE:-http://localhost:5173}"
BRIDGE="${NOTION3D_CURSOR_SDK_BRIDGE_BASE:-http://127.0.0.1:8787}"
HERMES="${NOTION3D_HERMES_API_BASE:-http://127.0.0.1:8642}"

fail=0

check() {
  local name="$1"
  local url="$2"
  if curl -sf "$url" >/dev/null; then
    echo "OK  $name  $url"
  else
    echo "FAIL $name  $url" >&2
    fail=1
  fi
}

echo "Notion3D stack check — AGENT=$AGENT"
check "API" "$API/health"

if [ "$AGENT" = "cursor_sdk" ]; then
  check "Bridge" "$BRIDGE/health"
fi

if [ "$AGENT" = "hermes" ]; then
  check "Hermes" "$HERMES/health"
fi

check "Web" "$WEB"

if [ "$fail" -eq 0 ]; then
  echo "---"
  curl -sf "$API/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print('web_chat_mode:', d.get('web_chat_mode')); print('forgecad:', d.get('forgecad_available')); print('openscad:', d.get('openscad_available')); print('bridge_ready:', d.get('agent_bridge_ready'))"
fi

exit "$fail"
