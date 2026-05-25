# 外部 Agent 经 MCP 接入

Notion3D Engine 不含 LLM。在 Cursor IDE、Claude Code 等环境中配置 `notion3d-mcp` 即可建模。

架构与 API 见 [architecture.md](../architecture.md)。工作流与 Skills 见 [AGENTS.md](../../AGENTS.md)。

## 1. 启动 Engine

```bash
make install
make dev AGENT=engine    # 或 make api（仅 Engine）
```

## 2. 安装 MCP

```bash
cd apps/mcp-server && pip install -e .
```

| 变量 | 默认 | 说明 |
|------|------|------|
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | Engine 地址 |

运行：`make mcp` 或 `notion3d-mcp`

## 3. 配置 Agent

| 场景 | 文档 |
|------|------|
| Web 工作台对话 | [agents/README.md](../agents/README.md) |
| Hermes | [agents/hermes.md](../agents/hermes.md) |
| Cursor / Claude Code | 在 MCP 配置中启动 `notion3d-mcp`（stdio） |

示例：`config/hermes-notion3d-mcp.yaml`

## 故障排查

| 现象 | 检查 |
|------|------|
| MCP 不可用 | `make api`；`notion3d_health` |
| ForgeCAD 失败 | `cd apps/forge-runner && npm install` |
| Web 无模型 | Agent 是否调用 `render_forge` + `wait_job` |
