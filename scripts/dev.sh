#!/usr/bin/env bash
# 按集成环境启动本地开发栈：make dev AGENT=<profile>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="${1:-}"

usage() {
  cat <<'EOF'
用法: make dev AGENT=<profile>

  cursor_sdk   默认 — CURSOR_API_KEY + agent-bridge + API + Web（Web 对话）
  hermes       Hermes gateway + API + Web（Web 对话）
  engine       仅 API + Web（无 Web 对话；MCP / 外部 Agent 调 Engine）

示例:
  make dev AGENT=cursor_sdk
  make dev AGENT=hermes
  make dev-cursor
EOF
}

case "$AGENT" in
  cursor_sdk | hermes | engine) ;;
  *)
    usage
    exit 1
    ;;
esac

set -a
[ -f "$ROOT/.env" ] && . "$ROOT/.env"
[ -f "$ROOT/apps/api/.env" ] && . "$ROOT/apps/api/.env"
set +a

export NOTION3D_AGENT_PROVIDER="$AGENT"
export NOTION3D_REPO_ROOT="$ROOT"
PYTHON="${PYTHON:-python3.11}"

port_in_use() {
  lsof -ti ":$1" >/dev/null 2>&1
}

preflight() {
  if [ "$AGENT" = "cursor_sdk" ]; then
    if [ -z "${CURSOR_API_KEY:-}" ]; then
      echo "错误: AGENT=cursor_sdk 需要 .env 中配置 CURSOR_API_KEY" >&2
      exit 1
    fi
    if [ ! -d "$ROOT/apps/agent-bridge/node_modules" ]; then
      echo "提示: 首次运行请执行 make install" >&2
    fi
  fi

  if [ "$AGENT" = "hermes" ]; then
    if ! command -v "${NOTION3D_HERMES_BIN:-hermes}" >/dev/null 2>&1; then
      echo "错误: 未找到 hermes CLI；见 docs/agents/hermes.md" >&2
      exit 1
    fi
    if ! command -v notion3d-mcp >/dev/null 2>&1; then
      echo "提示: notion3d-mcp 不在 PATH；Hermes 需配置 MCP，见 docs/agents/hermes.md" >&2
    fi
  fi
}

banner() {
  echo "Notion3D dev — AGENT=$AGENT"
  if [ "$AGENT" = "cursor_sdk" ]; then
    echo "  Bridge  http://127.0.0.1:${NOTION3D_AGENT_BRIDGE_PORT:-8787}"
  fi
  if [ "$AGENT" = "hermes" ]; then
    echo "  Hermes  ${NOTION3D_HERMES_API_BASE:-http://127.0.0.1:8642}"
  fi
  echo "  API     http://127.0.0.1:8000"
  echo "  Web     http://localhost:5173"
  [ "$AGENT" = "engine" ] && echo "  （无 Agent sidecar — Web 对话不可用）"
  echo "Ctrl+C 停止全部；或另开终端 make stop"
}

start_hermes_gateway() {
  local port="${NOTION3D_HERMES_API_PORT:-8642}"
  if port_in_use "$port"; then
    echo "Hermes gateway 已在 :$port 运行，跳过启动"
    return
  fi

  export API_SERVER_ENABLED=true
  if [ -n "${HERMES_API_SERVER_KEY:-${NOTION3D_HERMES_API_KEY:-}}" ]; then
    export API_SERVER_KEY="${HERMES_API_SERVER_KEY:-${NOTION3D_HERMES_API_KEY}}"
  fi
  export API_SERVER_PORT="$port"
  export API_SERVER_HOST="${NOTION3D_HERMES_API_HOST:-127.0.0.1}"

  echo "启动 Hermes gateway（:${port}）…"
  ( "${NOTION3D_HERMES_BIN:-hermes}" gateway ) &
}

preflight
banner
sleep 0.3

trap 'kill 0' INT TERM

if [ "$AGENT" = "cursor_sdk" ]; then
  ( cd "$ROOT/apps/agent-bridge" && npm start ) &
fi

if [ "$AGENT" = "hermes" ]; then
  start_hermes_gateway
fi

( cd "$ROOT/apps/api" && "$PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ) &
( cd "$ROOT/apps/web" && npm run dev ) &

wait
