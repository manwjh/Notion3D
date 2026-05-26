# Hermes 接入 Notion3D

Web 设计助手经 **Hermes gateway**（`:8642`）+ **notion3d MCP** 建模。

← [Agent 接入总览](README.md)

## 前置

1. 安装 [Hermes Agent](https://github.com/NousResearch/hermes-agent)（`hermes` 在 PATH）
2. 在 Hermes 配置 LLM provider（见 Hermes 文档）
3. `make install`（含 `notion3d-mcp`）

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

## 4. 验证

```bash
curl http://127.0.0.1:8642/health
curl -H "Authorization: Bearer change-me-local-dev" http://127.0.0.1:8642/v1/capabilities
curl -s http://127.0.0.1:8000/health | grep -E 'web_chat_mode|agent_active'
# web_chat_mode: agent · agent_active: hermes
```

## 架构

```
Web POST /turn → HermesAdapter → Hermes POST /v1/runs
  → Hermes Agent + notion3d MCP → Engine :8000
```

Session：`notion3d-{project_id}`。

## 参考

- [Hermes API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server)
- [Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)
