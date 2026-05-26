#!/usr/bin/env bash
# Quick health check. Usage:
#   WEB_TURN=off bash scripts/check-dev-stack.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="${WEB_TURN:-${AGENT:-off}}"
case "$RAW" in
  off | none | engine | "") WEB_TURN=off ;;
  bridge | cursor_sdk) WEB_TURN=bridge ;;
  gateway | hermes) WEB_TURN=gateway ;;
  *) echo "Unknown WEB_TURN/AGENT=$RAW" >&2; exit 1 ;;
esac

API="${NOTION3D_API_BASE:-http://127.0.0.1:8000}"
WEB="${NOTION3D_WEB_BASE:-http://localhost:5173}"
BRIDGE="${NOTION3D_WEB_TURN_BRIDGE_BASE:-http://127.0.0.1:8787}"
GATEWAY="${NOTION3D_WEB_TURN_GATEWAY_BASE:-http://127.0.0.1:8642}"

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

echo "Notion3D stack check — WEB_TURN=$WEB_TURN"
check "API" "$API/health"

if [ "$WEB_TURN" = "bridge" ]; then
  check "Bridge" "$BRIDGE/health"
fi

if [ "$WEB_TURN" = "gateway" ]; then
  check "Gateway" "$GATEWAY/health"
fi

check "Web" "$WEB"

if [ "$fail" -eq 0 ]; then
  echo "---"
  curl -sf "$API/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print('web_turn:', d.get('web_turn')); print('web_chat_mode:', d.get('web_chat_mode')); print('forgecad:', d.get('forgecad_available'))"
fi

exit "$fail"
