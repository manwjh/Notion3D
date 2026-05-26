# 外部 Agent 经 MCP 接入

Notion3D Engine 不含 LLM。Cursor IDE、Claude Code、OpenClaw 等配置 **notion3d-mcp** 即可建模。

Web 设计助手（cursor_sdk / hermes）见 [agents/README.md](../agents/README.md) — 不经本文档的 MCP 直连路径。

## 1. 启动 Engine

```bash
make install
make dev AGENT=engine
```

| 进程 | 端口 | 职责 |
|------|------|------|
| API | 8000 | Engine |
| Web | 5173 | 工作台预览 |

```bash
curl -s http://127.0.0.1:8000/health | grep forgecad_available
# true
```

## 2. 安装 MCP

```bash
cd apps/mcp-server && pip install -e .
```

| 变量 | 默认 | 说明 |
|------|------|------|
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | Engine 地址 |
| `NOTION3D_WEB_BASE` | `http://localhost:5173` | Web 项目链接（MCP 返回给 Agent） |

运行：`make mcp` 或 `notion3d-mcp`（stdio）

## 3. 按 Agent 环境配置

| Agent | 配置位置 | 文档 |
|-------|----------|------|
| OpenClaw | `~/.openclaw/openclaw.json` → `mcp.servers` | [agents/openclaw.md](../agents/openclaw.md) |
| Cursor IDE | `.cursor/mcp.json` | 见下文 |
| Claude Code | Claude MCP 配置 | `command: notion3d-mcp`，同上 env |
| Hermes（Web 对话） | `~/.hermes/config.yaml` | [agents/hermes.md](../agents/hermes.md) |

示例文件：

- [config/openclaw-notion3d-mcp.json](../../config/openclaw-notion3d-mcp.json)
- [config/hermes-notion3d-mcp.yaml](../../config/hermes-notion3d-mcp.yaml)
- [.cursor/mcp.json.example](../../.cursor/mcp.json.example)

### Cursor IDE

复制示例到项目根 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "notion3d": {
      "command": "notion3d-mcp",
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "NOTION3D_API_BASE": "http://127.0.0.1:8000",
        "NOTION3D_WEB_BASE": "http://localhost:5173"
      }
    }
  }
}
```

重启 Cursor 或 reload MCP。Skills 见 `.cursor/skills/`；工作流见 [AGENTS.md](../../AGENTS.md)。

## 4. MCP 工作流

```
notion3d_health()
notion3d_report_design_plan(...)
notion3d_render_forge(forge_code, files_json=...)
notion3d_wait_job(...)
notion3d_report_design_review(...)
```

改稿：`notion3d_get_forge_sources(version)` → 修改 → `render_forge`

## 5. Web 预览

建模完成后在 Web 打开项目：

```
http://localhost:5173/p/<project_id>
```

左栏支持参数调整、Forge 代码编辑、部件精修（点选部件树 → 跳转源码片段）。

## 故障排查

| 现象 | 检查 |
|------|------|
| MCP 不可用 | `make dev AGENT=engine`；`notion3d_health` |
| ForgeCAD 失败 | `cd apps/forge-runner && npm install` |
| Web 无模型 | Agent 是否调用 `render_forge` + `wait_job` |
| 链接打不开 | `NOTION3D_WEB_BASE` 与浏览器地址一致 |
