# Hermes 接入 Notion3D

Web 设计助手经 **Hermes gateway**（`:8642`）+ **notion3d MCP** 建模。

← [Agent 接入总览](README.md)

## 前置

1. 安装 [Hermes Agent](https://github.com/NousResearch/hermes-agent)（`hermes` 在 PATH）
2. 在 Hermes 配置 LLM provider（见 Hermes 文档）
3. `make install`（含 `notion3d-mcp`、`apps/forge-runner`）

## 1. 配置 notion3d MCP

将 [config/hermes-notion3d-mcp.yaml](../../config/hermes-notion3d-mcp.yaml) 合并进 `~/.hermes/config.yaml`：

```yaml
mcp_servers:
  notion3d:
    command: notion3d-mcp
    env:
      NOTION3D_API_BASE: http://127.0.0.1:8000
      NOTION3D_WEB_BASE: http://localhost:5173
```

或在 Hermes 项目目录安装 MCP 依赖后重启 gateway，并用 `/reload-mcp` 刷新工具列表。

局域网分享链接时，将 `NOTION3D_WEB_BASE` 改为 `http://<本机 IP>:5173`。

## 2. 启用 Hermes API Server

`~/.hermes/.env`：

```env
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
```

Notion3D 根目录 `.env` 使用同一 key：

```env
HERMES_API_SERVER_KEY=change-me-local-dev
```

## 3. 启动

```bash
make dev AGENT=hermes
```

`dev.sh` 会注入 `NOTION3D_AGENT_PROVIDER=hermes`，并启动 gateway（若 `:8642` 未监听）、API、Web。

手动启动 gateway（可选）：

```bash
hermes gateway
# 日志应含: API server listening on http://127.0.0.1:8642
```

## 4. 验证

```bash
curl http://127.0.0.1:8642/health
curl -H "Authorization: Bearer change-me-local-dev" http://127.0.0.1:8642/v1/capabilities
curl -s http://127.0.0.1:8000/health | grep -E 'web_chat_mode|agent_active|forgecad_available'
# web_chat_mode: agent · agent_active: hermes · forgecad_available: true
```

Web 设计助手面板应显示 **已连接**。

## 架构

```
Web POST /turn → HermesAdapter → Hermes POST /v1/runs
  → Hermes Agent + notion3d MCP → Engine :8000 → Web 预览
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
| MCP 连不上 Engine | dev 栈中 API 已起；`NOTION3D_API_BASE` |
| 有回复无模型 | Job 日志；是否调 `render_forge` + `wait_job` |

## 参考

- [Hermes API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server)
- [Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)
- [AGENTS.md](../../AGENTS.md) — MCP 工具与工作流
