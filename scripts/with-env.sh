#!/usr/bin/env bash
# 加载仓库根目录 .env，再启动命令（make api / dev 共用）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a
[ -f "$ROOT/.env" ] && . "$ROOT/.env"
[ -f "$ROOT/apps/api/.env" ] && . "$ROOT/apps/api/.env"
set +a
exec "$@"
