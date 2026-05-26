#!/usr/bin/env bash
# Notion3D local dev — Engine + Web; optional Web Turn sidecar (interface-based).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# WEB_TURN=off|bridge|gateway  —  AGENT= legacy alias (engine→off, cursor_sdk→bridge, hermes→gateway)
RAW="${WEB_TURN:-${AGENT:-off}}"

normalize_web_turn() {
  case "$1" in
    off | none | engine | "") echo "off" ;;
    bridge | cursor_sdk) echo "bridge" ;;
    gateway | hermes) echo "gateway" ;;
    *)
      echo "错误: 未知 WEB_TURN/AGENT=$1（可用: off | bridge | gateway）" >&2
      exit 1
      ;;
  esac
}

WEB_TURN="$(normalize_web_turn "$RAW")"

usage() {
  cat <<'EOF'
用法: make dev [WEB_TURN=<interface>]

  off       默认 — Engine + Web（MCP 外部 Agent + 手动编辑）
  bridge    附加 agent-bridge :8787（浏览器内 POST /turn）
  gateway   附加 HTTP Runs gateway :8642（浏览器内 POST /turn）

示例:
  make dev
  make dev WEB_TURN=bridge
  make dev WEB_TURN=gateway

兼容旧参数（将移除）:
  AGENT=engine → off · AGENT=cursor_sdk → bridge · AGENT=hermes → gateway
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

set -a
[ -f "$ROOT/.env" ] && . "$ROOT/.env"
[ -f "$ROOT/apps/api/.env" ] && . "$ROOT/apps/api/.env"
set +a

export NOTION3D_WEB_TURN="$WEB_TURN"
export NOTION3D_REPO_ROOT="$ROOT"
PYTHON="${PYTHON:-python3.11}"
export NOTION3D_PYTHON="$PYTHON"

port_in_use() {
  lsof -ti ":$1" >/dev/null 2>&1
}

preflight() {
  if [ "$WEB_TURN" = "bridge" ]; then
    if [ -z "${CURSOR_API_KEY:-}" ]; then
      echo "错误: WEB_TURN=bridge 需要 .env 中配置 CURSOR_API_KEY" >&2
      exit 1
    fi
    if [ ! -d "$ROOT/apps/agent-bridge/node_modules" ]; then
      echo "提示: 首次运行请执行 make install" >&2
    fi
    if ! "$PYTHON" -c "import notion3d_mcp" 2>/dev/null; then
      echo "错误: 未安装 notion3d-mcp。请执行: cd apps/mcp-server && $PYTHON -m pip install -e ." >&2
      exit 1
    fi
  fi

  if [ "$WEB_TURN" = "gateway" ]; then
    if ! command -v "${NOTION3D_WEB_TURN_GATEWAY_BIN:-${NOTION3D_HERMES_BIN:-hermes}}" >/dev/null 2>&1; then
      echo "错误: WEB_TURN=gateway 需要 gateway CLI 在 PATH；见 docs/agents/web-turn-gateway.md" >&2
      exit 1
    fi
  fi
}

banner() {
  echo "Notion3D dev — WEB_TURN=$WEB_TURN"
  if [ "$WEB_TURN" = "bridge" ]; then
    echo "  Bridge  http://127.0.0.1:${NOTION3D_WEB_TURN_BRIDGE_PORT:-8787}"
  fi
  if [ "$WEB_TURN" = "gateway" ]; then
    echo "  Gateway ${NOTION3D_WEB_TURN_GATEWAY_BASE:-http://127.0.0.1:8642}"
  fi
  echo "  API     http://127.0.0.1:8000"
  echo "  Web     http://localhost:5173  （本机）"
  local lan_ip=""
  if command -v ipconfig >/dev/null 2>&1; then
    for iface in en0 en1; do
      lan_ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
      [ -n "$lan_ip" ] && break
    done
  elif command -v hostname >/dev/null 2>&1; then
    lan_ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  fi
  if [ -n "$lan_ip" ]; then
    echo "          http://${lan_ip}:5173  （局域网）"
  fi
  if [ "$WEB_TURN" = "off" ]; then
    echo "  MCP     外部 Agent 宿主配置 notion3d-mcp → Engine（见 docs/agents/README.md）"
  fi
  echo "Ctrl+C 停止全部；或另开终端 make stop"
}

wait_http() {
  local url="$1"
  local label="$2"
  local max="${3:-45}"
  local i=1
  while [ "$i" -le "$max" ]; do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "  ✓ $label"
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  echo "  ✗ $label 未在 ${max}s 内就绪: $url" >&2
  return 1
}

start_gateway() {
  local port="${NOTION3D_WEB_TURN_GATEWAY_PORT:-8642}"
  if port_in_use "$port"; then
    echo "Web Turn gateway 已在 :$port 运行，跳过启动"
    return
  fi

  export API_SERVER_ENABLED=true
  if [ -n "${HERMES_API_SERVER_KEY:-${NOTION3D_WEB_TURN_GATEWAY_API_KEY:-${NOTION3D_HERMES_API_KEY:-}}}" ]; then
    export API_SERVER_KEY="${HERMES_API_SERVER_KEY:-${NOTION3D_WEB_TURN_GATEWAY_API_KEY:-${NOTION3D_HERMES_API_KEY}}}"
  fi
  export API_SERVER_PORT="$port"
  export API_SERVER_HOST="${NOTION3D_WEB_TURN_GATEWAY_HOST:-127.0.0.1}"

  local bin="${NOTION3D_WEB_TURN_GATEWAY_BIN:-${NOTION3D_HERMES_BIN:-hermes}}"
  echo "启动 Web Turn gateway（:${port}）…"
  ( "$bin" gateway ) &
}

preflight
banner
sleep 0.3

trap 'kill 0' INT TERM

if [ "$WEB_TURN" = "bridge" ]; then
  ( cd "$ROOT/apps/agent-bridge" && NOTION3D_PYTHON="$PYTHON" npm start ) &
  wait_http "http://127.0.0.1:${NOTION3D_WEB_TURN_BRIDGE_PORT:-8787}/health" "Bridge :8787" 60 || true
fi

if [ "$WEB_TURN" = "gateway" ]; then
  start_gateway
  wait_http "${NOTION3D_WEB_TURN_GATEWAY_BASE:-http://127.0.0.1:8642}/health" "Web Turn gateway" 60 || true
fi

( cd "$ROOT/apps/api" && "$PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ) &
wait_http "http://127.0.0.1:8000/health" "API :8000" 45 || true
( cd "$ROOT/apps/web" && npm run dev ) &

wait
