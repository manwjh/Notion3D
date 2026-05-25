# Notion3D 架构

Notion3D = **ForgeCAD 装配渲染引擎** + **Web 工作台**。不含 LLM。

## 三层边界

```
┌─────────────────────────────────────────────────────────────┐
│  Engine（apps/api）— 无 LLM                                  │
│  项目 / Design Turn / Job / ForgeCAD 渲染 / 版本 / 持久化    │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   apps/web           apps/mcp-server    Web Agent 对话
   观察·点选·导出      Agent 工具层        → Adapter → 外部 LLM
   高级=手动模式
```

| 层 | 目录 | 职责 |
|----|------|------|
| **Engine** | `apps/api` | CRUD、Design Turn、Job 队列、`render-forge`、版本 |
| **MCP** | `apps/mcp-server` | `notion3d_*` tools → HTTP 调 Engine |
| **Templates** | `templates/builtin/` | Forge 演示模板 |
| **Adapter** | `apps/api/.../agents` + `apps/agent-bridge` | Web 对话 |
| **Web** | `apps/web` | 工作台 UI |

## Design Turn

```
intake → plan → author → render → review → done
         ↓ report_design_plan    ↓ render_forge    ↓ report_design_review
```

详见 [design-pipeline.md](design-pipeline.md)。

## 客户端路径

**A. 外部 Agent** — `notion3d_render_forge` → `notion3d_wait_job`

**B. Web 对话** — `POST /turn` → Adapter → Agent → MCP → Engine

**C. 手动编辑** — Web 左栏改 `.forge.js` → `POST /render-forge`

## Engine API

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/projects/{id}/render-forge` | 提交 ForgeCAD |
| POST | `/api/projects/{id}/turn` | Web 对话入口 |
| GET | `/api/projects/{id}/jobs/{job_id}` | Job 状态 |
| GET | `/api/templates` | 模板列表 |
| POST | `/api/templates/{id}/apply` | 应用演示模板 |
| GET | `/api/projects/{id}/state` | 项目快照 |

## MCP Tools

| Tool | Engine |
|------|--------|
| `notion3d_render_forge` | `POST .../render-forge` |
| `notion3d_get_forge_sources` | 读取 `model.forge.js` + `src/` |
| `notion3d_report_design_plan` | plan 阶段 |
| `notion3d_report_design_review` | review 阶段 |
| `notion3d_apply_template` | 应用模板 |
| `notion3d_wait_job` | 轮询 Job |

## 数据

```
data/projects/{id}/
  meta.json · messages.json
  versions/{n}/
    model.forge.js · model.stl · parts.json · parts/*.stl
```

## 环境变量

```env
CURSOR_API_KEY=...
NOTION3D_AGENT_PROVIDER=cursor_sdk
NOTION3D_WEB_BASE=http://localhost:5173
NOTION3D_API_BASE=http://127.0.0.1:8000   # MCP 侧
```
