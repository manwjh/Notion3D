# Web Turn · gateway

**接口 2** 的一种 sidecar：HTTP Runs API（默认 `:8642`）→ Agent 运行时 → notion3d-mcp → Engine。

← [Agent 接入总览](README.md)

## 部署

```env
NOTION3D_WEB_TURN=gateway
NOTION3D_WEB_TURN_GATEWAY_BIN=hermes
NOTION3D_WEB_TURN_GATEWAY_BASE=http://127.0.0.1:8642
HERMES_API_SERVER_KEY=change-me-local-dev
```

Gateway 宿主侧还需配置 notion3d MCP 与 LLM（见宿主文档）。

```bash
make install
make dev WEB_TURN=gateway
```

## Gateway API Server

在 gateway 宿主 `~/.hermes/.env`（示例）：

```env
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
```

合并 [config/hermes-notion3d-mcp.yaml](../../config/hermes-notion3d-mcp.yaml) 到 MCP 配置。

## 验证

```bash
curl -s http://127.0.0.1:8642/health
curl -s http://127.0.0.1:8000/health | grep web_chat_mode
```

Session ID：`notion3d-{project_id}`。

## 数据流

```
Web POST /turn → Engine → gateway :8642 → Agent + notion3d-mcp → Engine → Web 预览
```
