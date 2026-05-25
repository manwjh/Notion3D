# Notion3D 架构

Notion3D = **ForgeCAD 装配渲染引擎** + **Web 工作台**。不含 LLM。

> OpenSCAD 已降级为 legacy 路径，见 [docs/cad-backend-v2.md](cad-backend-v2.md)。

## 三层边界

```
┌─────────────────────────────────────────────────────────────┐
│  Engine（apps/api）— 无 LLM                                  │
│  项目 / Design Turn / Job / OpenSCAD 渲染 / 版本 / 持久化      │
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
| **Engine** | `apps/api` | CRUD、Design Turn、Job 队列、`render-scad`、版本 |
| **MCP** | `apps/mcp-server` | `notion3d_*` tools → HTTP 调 Engine |
| **Templates** | `templates/builtin/` | 内置 SCAD 模板库（只读数据） |
| **Adapter** | `apps/api/.../agents` + `apps/agent-bridge` | Web 对话；转发到外部 Agent |
| **Web** | `apps/web` | 工作台 UI；不存 LLM Key |

## Design Turn（设计轮次）

一次用户输入 = 一个 **Design Turn**，分 **设计阶段** 与 **运行相位**：

```
intake → plan → author → render → review → done
         ↓ report_design_plan    ↓ render_scad    ↓ report_design_review
```

- `design_phase`：intake | plan | author | render | review | done | blocked
- `agent_phase` / `render_phase`：对话与 Job 状态
- `plan` / `review`：Agent 经 MCP 写入的结构化产物

详见 **[docs/design-pipeline.md](design-pipeline.md)**。

- `meta.active_turn`：进行中的轮次
- Job 带 `turn_id` + `source`（`agent` | `manual` | `template`）
- Version meta 带 `turn_id` / `job_id` / `validation_warnings`

Web `/state` 返回 `active_turn`，Chat 用 `job_id` / `turn_id` 关联版本按钮。

## 两条客户端路径

### A. 外部 Agent（推荐）

```
Agent（自带 LLM）→ notion3d-mcp → Engine REST → data/projects/
                                              ↘ Web 预览（共享 data/）
```

主路径：`notion3d_render_forge`（`source=agent`，绑定 active turn）→ `notion3d_wait_job`。

Legacy：`notion3d_render_scad`。`notion3d_template` 仅 dev/极简 primitive。

### B. Web 对话

```
Web → POST /api/projects/{id}/turn
    → 创建 turn_id + user 消息
    → Adapter（cursor_sdk | hermes）
    → 外部 Agent → notion3d MCP → Engine（job 绑定 turn）
```

**必须**配置 Agent，见 [docs/agents/README.md](agents/README.md)。

### C. 手动模式（高级编辑）

Web **高级编辑** → `POST /render-forge` 或 legacy `/render-scad`（`source=manual`）。

## 进程（本地开发）

```bash
make dev AGENT=cursor_sdk   # API :8000 + bridge :8787 + Web :5173
```

| 进程 | 何时需要 |
|------|----------|
| `make api` | 必须 |
| `make web` | 工作台 |
| `make bridge` | Web 对话 + `cursor_sdk` |
| `notion3d-mcp` | 外部 Agent / bridge 内 spawn |

## Engine API 要点

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/projects/{id}/render-forge` | 提交 ForgeCAD（主路径） |
| POST | `/api/projects/{id}/render-scad` | Legacy OpenSCAD |
| POST | `/api/projects/{id}/jobs/template` | 规则模板（dev only） |
| GET | `/api/projects/{id}/jobs/{job_id}` | Job 状态 |
| POST | `/api/projects/{id}/turn` | **Web 主入口**：创建 turn + 转发 Agent |
| GET | `/api/templates` | 模板库列表 |
| GET | `/api/templates/{id}` | 模板详情（含 forge_code / scad_code） |
| POST | `/api/templates/{id}/apply` | 应用模板到项目 |
| POST | `/api/projects/{id}/versions/{v}/save-template` | 另存为用户模板 |
| GET | `/api/projects/{id}/state` | 快照（messages + active_turn + job + agent） |

## MCP Tools

| Tool | 调用的 Engine |
|------|---------------|
| `notion3d_render_forge` | `POST .../render-forge` |
| `notion3d_render_scad` | `POST .../render-scad`（legacy） |
| `notion3d_list_templates` | `GET /api/templates` |
| `notion3d_apply_template` | `POST /api/templates/{id}/apply` |
| `notion3d_save_template` | `POST .../versions/{v}/save-template` |
| `notion3d_template` | `POST .../jobs/template`（legacy） |
| `notion3d_wait_job` | 轮询 `GET .../jobs/{id}` |

## 数据

```
data/
  projects/{id}/
    meta.json          # agent_session_id、agent_run_pending、active_turn
    messages.json      # user / assistant / system；turn_id、job_id
    versions/{n}/
      meta.json        # turn_id、job_id、prompt
      model.forge.js   # 或 legacy model.scad
      model.stl
      parts.json
      parts/{id}.stl
  jobs/{id}.json       # turn_id、source
```

Agent 与 Web 通过 **同一 `data/` 目录** 共享项目，不直连。

## 环境变量

根目录 `.env`：

```env
CURSOR_API_KEY=...              # cursor_sdk
HERMES_API_SERVER_KEY=...       # hermes（与 ~/.hermes/.env 一致）
NOTION3D_AGENT_PROVIDER=cursor_sdk    # cursor_sdk | hermes | engine
NOTION3D_WEB_BASE=http://localhost:5173
```

MCP（Agent 侧）：

```env
NOTION3D_API_BASE=http://127.0.0.1:8000
```
