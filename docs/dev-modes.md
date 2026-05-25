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

## cursor_sdk（当前默认联调路径）

| 进程 | 端口 | 职责 |
|------|------|------|
| agent-bridge | 8787 | `@cursor/sdk` + notion3d MCP |
| API | 8000 | Engine |
| Web | 5173 | 工作台 |

**前置**

1. `.env` 中 `CURSOR_API_KEY`
2. `make install`（含 `apps/forge-runner` ForgeCAD）
3. OpenSCAD 可选（legacy 模板）

**数据流**

```
Web POST /turn → API turn_service → bridge POST /v1/turn
  → Cursor Agent（project Skills + MCP）
  → notion3d MCP → API render-forge → ForgeCAD → Web 装配预览
```

**常见故障**

| 现象 | 原因 | 处理 |
|------|------|------|
| 助手显示「未连接」 | bridge 未就绪或 Key 无效 | 看 bridge 日志；`curl :8787/health` |
| 对话 blocked / no_agent | sidecar 未通过 ready 检测 | 等 dev.sh 打印 ✓ Bridge；刷新 Web |
| 有回复无模型 | Agent 未调 MCP 或 render 失败 | 看 API job message、对话 system 消息 |
| active_turn 卡住 | 旧版 review 未结束 | 已修复：render 成功后 Engine 自动 pass review |
| MCP 工具不可用 | `notion3d-mcp` 不在 bridge PATH | dev.sh 预检；bridge 用 `python -m notion3d_mcp.server` |

## hermes

见 [agents/hermes.md](agents/hermes.md)。需 `hermes gateway` + `~/.hermes` MCP 配置。

## engine

无 Agent sidecar。Web 对话不可用；可用 **高级编辑** 手动改 ForgeCAD/OpenSCAD，或外部 Agent 经 MCP 建模。

## 设计流水线（各模式通用）

Agent 应：`report_design_plan` → `render_forge`（或 legacy `render_scad`）→ `wait_job` → `report_design_review`。

若 Agent 跳过 plan/review，Engine 会：

- 渲染前自动生成 **implicit plan**
- 渲染成功且 Agent 已回复时 **自动 pass review**

详见 [design-pipeline.md](design-pipeline.md)。
