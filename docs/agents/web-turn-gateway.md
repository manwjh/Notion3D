# Web Turn · gateway

**接口 2** 的一种 sidecar：HTTP Runs API（默认 `:8642`）→ Agent 运行时 → notion3d-mcp → Engine。

← [Agent 接入总览](README.md) · 完整依赖表：[dependencies.md](../dependencies.md)

> **接口名 `gateway`，当前实现为 Hermes**（HTTP Runs 宿主）。环境变量保留 `HERMES_*` / `NOTION3D_HERMES_*` 别名；`NOTION3D_WEB_TURN_GATEWAY_BIN` 默认为 `hermes`。

## Sidecar 依赖

| 组件 | 来源 | 说明 |
|------|------|------|
| **gateway CLI** | 外部安装 | 须在 PATH；默认 `hermes` |
| **HTTP Runs API** | gateway 宿主 | 默认 `:8642`；`API_SERVER_ENABLED=true` |
| **notion3d-mcp** | 仓库 `apps/mcp-server` | 配置在 **gateway 宿主** MCP，非 Engine 进程 |
| **LLM** | gateway 宿主 | 如 `~/.hermes/config.yaml`；**不在 Notion3D** |

Notion3D Engine 仅通过 HTTP adapter 连 gateway；不 bundled gateway 二进制。

## 部署

```env
NOTION3D_WEB_TURN=gateway
NOTION3D_WEB_TURN_GATEWAY_BIN=hermes
NOTION3D_WEB_TURN_GATEWAY_BASE=http://127.0.0.1:8642
HERMES_API_SERVER_KEY=change-me-local-dev
```

Gateway 宿主侧还需配置 notion3d MCP 与 LLM（见下文）。

```bash
make install
make dev WEB_TURN=gateway
```

`make dev` 会检查 gateway CLI 是否在 PATH。

## Gateway API Server（Hermes 示例）

在 gateway 宿主 `~/.hermes/.env`：

```env
API_SERVER_ENABLED=true
API_SERVER_KEY=change-me-local-dev
```

`API_SERVER_KEY` 须与 Notion3D `.env` 中 `HERMES_API_SERVER_KEY` **一致**。

合并 [config/hermes-notion3d-mcp.yaml](../../config/hermes-notion3d-mcp.yaml) 到 MCP 配置。LLM provider keys 在 gateway 宿主配置，不在 Notion3D。

## 验证

```bash
curl -s http://127.0.0.1:8642/health
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
# web_turn: gateway · web_chat_mode: agent（就绪时）
```

Session ID：`notion3d-{project_id}`。

## 数据流

```
Web POST /turn → Engine → gateway :8642 → Hermes Agent + notion3d-mcp → Engine → Web 预览
```

## 故障排查

| 现象 | 检查 |
|------|------|
| `dev.sh` 报 CLI 不在 PATH | 安装 Hermes；或设置 `NOTION3D_WEB_TURN_GATEWAY_BIN` |
| gateway 401 | `HERMES_API_SERVER_KEY` 与宿主 `API_SERVER_KEY` 一致 |
| Agent 不调 MCP | 宿主 MCP 配置；合并 `hermes-notion3d-mcp.yaml` |
