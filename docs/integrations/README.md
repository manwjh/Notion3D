# 外部 Agent 经 MCP 接入

Notion3D Engine 不含 LLM。Cursor IDE、Claude Code、OpenClaw 等配置 **notion3d-mcp** 即可建模。

Web 设计助手（cursor_sdk / hermes）见 [agents/README.md](../agents/README.md)。

## 1. 启动 Engine

```bash
make install
make dev AGENT=engine
```

## 2. 安装 MCP

```bash
cd apps/mcp-server && pip install -e .
```

| 变量 | 默认 | 说明 |
|------|------|------|
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | Engine 地址 |

## 3. 按 Agent 环境配置

| Agent | 配置位置 | 文档 |
|-------|----------|------|
| OpenClaw | `~/.openclaw/openclaw.json` → `mcp.servers` | [agents/openclaw.md](../agents/openclaw.md) |
| Cursor IDE | `.cursor/mcp.json` | 见 [.cursor/mcp.json.example](../../.cursor/mcp.json.example) |
| Claude Code | Claude MCP 配置 | `command: notion3d-mcp`，同上 env |
| Hermes（Web 对话） | `~/.hermes/config.yaml` | [agents/hermes.md](../agents/hermes.md) |

示例文件：

- [config/openclaw-notion3d-mcp.json](../../config/openclaw-notion3d-mcp.json)
- [config/hermes-notion3d-mcp.yaml](../../config/hermes-notion3d-mcp.yaml)

## 4. 预览

建模完成后在 Web 打开项目：

```
http://localhost:5173/p/<project_id>
```
