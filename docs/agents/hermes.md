# Hermes Agent 接入 Notion3D

Web 对话经 **Hermes Agent** 本地 gateway（HTTP API）+ **notion3d MCP** 建模。

## 前置

1. 安装 [Hermes Agent](https://github.com/NousResearch/hermes-agent)（`hermes` 在 PATH）
2. 在 Hermes 中配置 LLM provider（OpenRouter、Anthropic 等 — 见 Hermes 文档）
3. 本仓库已安装 MCP：`make install` → `notion3d-mcp` 在 PATH

## 1. 配置 notion3d MCP

将 [config/hermes-notion3d-mcp.yaml](../../config/hermes-notion3d-mcp.yaml) 中的 `notion3d` 块合并进 `~/.hermes/config.yaml`：

```yaml
mcp_servers:
  notion3d:
    command: notion3d-mcp
    env:
      NOTION3D_API_BASE: http://127.0.0.1:8000
      NOTION3D_WEB_BASE: http://localhost:5173
```

或在 Hermes 项目目录安装 MCP 依赖后重启 gateway，并用 `/reload-mcp` 刷新工具列表。

## 2. 启用 API Server

在 `~/.hermes/.env` 添加：

```env
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
```

Notion3D 侧在根目录 `.env` 使用同一 key（任选其一）：

```env
HERMES_API_SERVER_KEY=change-me-local-dev
NOTION3D_AGENT_PROVIDER=hermes
```

## 3. 启动

```bash
make dev AGENT=hermes
# 或
make dev-hermes
```

脚本会：

1. 若 `:8642` 无监听，启动 `hermes gateway`
2. 启动 API `:8000` 与 Web `:5173`
3. 注入 `NOTION3D_AGENT_PROVIDER=hermes`

手动启动 gateway（可选）：

```bash
hermes gateway
# 日志应含: API server listening on http://127.0.0.1:8642
```

## 4. 验证

```bash
curl http://127.0.0.1:8642/health
curl -H "Authorization: Bearer change-me-local-dev" http://127.0.0.1:8642/v1/capabilities
curl http://127.0.0.1:8000/health
```

`/health` 中 `agent_active` 应为 `hermes`，`web_chat_mode` 为 `agent`。

## 架构

```
Web → POST /api/projects/{id}/turn
    → HermesAdapter → Hermes POST /v1/runs
    → Hermes Agent + notion3d MCP → Engine :8000
```

Hermes 使用 **Runs API**（`POST /v1/runs`、`GET /v1/runs/{id}`），按 `session_id`（`notion3d-{project_id}`）保持多轮上下文。

## 与 Cursor SDK 对比

| | Cursor SDK | Hermes |
|---|------------|--------|
| Sidecar | `apps/agent-bridge` :8787 | `hermes gateway` :8642 |
| LLM Key | `CURSOR_API_KEY` | Hermes `~/.hermes` 配置 |
| MCP | bridge 内 spawn | `~/.hermes/config.yaml` |
| 启动 | `make dev AGENT=cursor_sdk` | `make dev AGENT=hermes` |

## 故障排查

| 现象 | 检查 |
|------|------|
| Web 显示「待连接助手」 | `curl :8642/health`；`NOTION3D_AGENT_PROVIDER=hermes` |
| 401 / 403 | `.env` 与 `~/.hermes/.env` 的 `API_SERVER_KEY` 一致 |
| Agent 不调用 MCP | `~/.hermes/config.yaml` 中 notion3d 块；gateway 日志；`/reload-mcp` |
| MCP 连不上 Engine | 先 `make api` 或 dev 栈中 API 已起；`NOTION3D_API_BASE` |

参考：[Hermes API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server)、[Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)
