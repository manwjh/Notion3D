# 本地开发模式

```bash
make dev AGENT=cursor_sdk   # Web 对话 + Cursor SDK bridge
make dev AGENT=hermes       # Web 对话 + Hermes gateway
make dev AGENT=engine       # 仅 Engine + Web（无 Web 对话）
```

启动后自检：

```bash
AGENT=cursor_sdk bash scripts/check-dev-stack.sh
```

## cursor_sdk（默认）

| 进程 | 端口 | 职责 |
|------|------|------|
| agent-bridge | 8787 | `@cursor/sdk` + notion3d MCP |
| API | 8000 | Engine |
| Web | 5173 | 工作台 |

**前置**：`.env` 中 `CURSOR_API_KEY` · `make install`（含 forge-runner）

**数据流**

```
Web POST /turn → bridge → Cursor Agent（Skills + MCP）
  → render-forge → ForgeCAD → Web 装配预览
```

**常见故障**

| 现象 | 处理 |
|------|------|
| 助手「未连接」 | 检查 bridge :8787 / `CURSOR_API_KEY` |
| 有回复无模型 | 看 job 日志；Agent 是否调 `render_forge` |
| MCP 不可用 | dev.sh 预检；`python -m notion3d_mcp.server` |

## hermes

见 [agents/hermes.md](agents/hermes.md)。

## engine

无 Web 对话。可用手动编辑 ForgeCAD，或外部 Agent 经 MCP 建模。

## 设计流水线

Agent：`report_design_plan` → `render_forge` → `wait_job` → `report_design_review`。

Engine 会在 Agent 跳步时自动生成 implicit plan / 自动 pass review。详见 [design-pipeline.md](design-pipeline.md)。
