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
   手动=参数/代码/精修
```

| 层 | 目录 | 职责 |
|----|------|------|
| **Engine** | `apps/api` | CRUD、Design Turn、Job 队列、`render-forge`、版本 |
| **MCP** | `apps/mcp-server` | `notion3d_*` tools → HTTP 调 Engine |
| **Templates** | `templates/builtin/` | Forge 演示模板 |
| **Adapter** | `apps/api/.../agents` + `apps/agent-bridge` | Web 对话（cursor_sdk / hermes） |
| **Web** | `apps/web` | 工作台 UI |
| **Forge Runner** | `apps/forge-runner` | ForgeCAD CLI 导出 STL + `parts.json` |

## Design Turn

```
intake → plan → author → render → review → done
         ↓ report_design_plan    ↓ render_forge    ↓ report_design_review
```

详见 [design-pipeline.md](design-pipeline.md)。

## 客户端路径

| 路径 | 入口 | Agent 环境 |
|------|------|------------|
| **A. MCP** | `notion3d_render_forge` → `wait_job` | OpenClaw、Cursor IDE、Claude Code |
| **B. Web 对话** | `POST /turn` → Adapter | cursor_sdk、hermes |
| **C. 手动编辑** | Web 左栏 → `POST /render-forge` | engine（无 sidecar） |

接入说明：[agents/README.md](agents/README.md)

路径 C 支持：参数面板、`param()` 即时预览（Forge 实时）、Forge 代码编辑、**部件精修**（`parts.json` 中 `source_ref` 映射源码位置）。

## Engine API

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/projects/{id}/render-forge` | 提交 ForgeCAD |
| POST | `/api/projects/{id}/turn` | Web 对话入口 |
| GET | `/api/projects/{id}/jobs/{job_id}` | Job 状态 |
| GET | `/api/templates` | 模板列表 |
| POST | `/api/templates/{id}/apply` | 应用演示模板 |
| GET | `/api/projects/{id}/state` | 项目快照 |
| POST | `/api/projects/{id}/versions/{v}/forge-preview` | 同步 Forge 实时预览 |

## MCP Tools

| Tool | Engine |
|------|--------|
| `notion3d_health` | `/health` |
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
    src/*.forge.js                    # 可选多文件
```

`parts.json` 每项可含 `source_ref`（主脚本或 `src/` 文件中的变量/片段），供 Web 部件精修跳转。

## 环境变量

```env
# Web 对话（make dev 注入 NOTION3D_AGENT_PROVIDER）
CURSOR_API_KEY=...                      # cursor_sdk
HERMES_API_SERVER_KEY=...               # hermes

NOTION3D_WEB_BASE=http://localhost:5173
NOTION3D_API_BASE=http://127.0.0.1:8000   # MCP 侧
```

Agent 接入详情：[agents/README.md](agents/README.md)
