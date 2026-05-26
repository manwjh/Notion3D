# Notion3D 架构

Notion3D = **ForgeCAD 装配渲染引擎** + **Web 工作台**。不含 LLM。

## 模块边界

```
┌─────────────────────────────────────────────────────────────┐
│  Engine（apps/api）— 无 LLM                                  │
│  项目 / Design Turn / Job / ForgeCAD 渲染 / 版本 / 持久化    │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   apps/web           apps/mcp-server    Web Turn（可选）
   观察·点选·导出      接口 1：MCP        接口 2：POST /turn
   手动=参数/代码/精修
```

| 层 | 目录 | 职责 |
|----|------|------|
| **Engine** | `apps/api` | CRUD、Design Turn、Job 队列、Forge 渲染、版本 |
| **Web** | `apps/web` | 三栏工作台 — 用户唯一界面 |
| **MCP** | `apps/mcp-server` | `notion3d_*` tools → Engine REST |
| **Web Turn** | `apps/api/.../agents/` + `apps/agent-bridge` | 浏览器对话 sidecar（`bridge` / `gateway`） |
| **Forge Runner** | `apps/forge-runner` | ForgeCAD CLI → STL + `parts.json` |

渲染细节见 [cad-backend-v2.md](cad-backend-v2.md)。**依赖、LLM 归属、环境变量**见 [dependencies.md](dependencies.md)。

## 部署模型（Local / LAN）

Engine 使用 **JSON 文件持久化**（`data/projects/`、`data/jobs/`），Job 状态在进程内缓存。设计假设：

- **单 uvicorn 进程**（`make dev` / Docker 默认 CMD 均如此）
- **无 API 鉴权** — 适合本机 `localhost` 或受控局域网
- 多 worker、多实例、公网 SaaS 需另行引入共享存储与鉴权（见 [dev-modes.md](dev-modes.md) § Engine 部署约束）

## 客户端路径（平行）

| 路径 | 技术接口 | 说明 |
|------|----------|------|
| **A. MCP** | `notion3d-mcp` | Agent 宿主（OpenClaw 等）调 Engine；Web 预览 |
| **B. Web 对话** | `POST /turn` → Web Turn sidecar | 可选；部署 `WEB_TURN=bridge\|gateway` |
| **C. 手动** | Web → `POST /render-forge` | 左栏编辑，无 LLM |

接入说明：[agents/README.md](agents/README.md)

## Design Turn

```
intake → plan → author → render → review → done | blocked
```

Engine 兜底见 [design-pipeline.md](design-pipeline.md)。

## Engine API（摘要）

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/health` | 工作台 / Forge / `web_turn` 状态 |
| POST | `/api/projects/{id}/turn` | Web 对话（需 Web Turn sidecar） |
| POST | `/api/projects/{id}/render-forge` | Forge 渲染（Agent 或手动） |

完整表见下文及 [agents/README.md](agents/README.md)。

### 健康

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/health` | `forgecad_available`、`web_turn`、`web_chat_mode` |

### 项目

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/projects` | 项目列表 |
| POST | `/api/projects` | 创建项目 |
| GET | `/api/projects/{id}/state` | 快照（messages、job、capabilities） |
| GET | `/api/projects/{id}/state/events` | 项目状态 SSE（Web Agent 对话进度） |

### Web 对话

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/projects/{id}/turn` | 浏览器自然语言入口 |

### Design Turn 制品

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/projects/{id}/design/plan` | plan（MCP: `report_design_plan`） |
| POST | `/api/projects/{id}/design/review` | review（MCP: `report_design_review`） |

### 渲染与 Job

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/projects/{id}/render-forge` | 提交 ForgeCAD |
| GET | `/api/projects/{id}/jobs/{job_id}` | Job 状态 |
| GET | `/api/projects/{id}/jobs/{job_id}/events` | Job SSE 推送（Web / MCP 实时进度） |

### 版本与产物

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/projects/{id}/versions` | 版本列表 |
| GET | `/api/projects/{id}/versions/{v}/parts.json` | 部件清单（含 `source_ref`） |
| POST | `/api/projects/{id}/versions/{v}/forge-preview` | Forge 实时预览 |
| GET | `/api/templates` | 模板列表 |

## MCP Tools

真源：`apps/mcp-server/notion3d_mcp/server.py`。完整列表：

`notion3d_health` · `notion3d_report_design_plan` · `notion3d_render_forge` · `notion3d_wait_job` · `notion3d_report_design_review` · `notion3d_get_forge_sources` · `notion3d_apply_template` · `notion3d_list_projects` · `notion3d_create_project` · `notion3d_get_job` · `notion3d_list_active_jobs` · `notion3d_list_versions` · `notion3d_list_templates` · `notion3d_get_template` · `notion3d_save_template` · `notion3d_list_messages` · `notion3d_get_design_state` · `notion3d_get_project_state` · `notion3d_wait_agent`

主路径：`notion3d_health` · `report_design_plan` · `render_forge` · `wait_job` · `report_design_review`

完整表见 [AGENTS.md](../AGENTS.md)。

## 环境变量（部署层）

完整索引：[dependencies.md](dependencies.md)

```env
NOTION3D_API_BASE=http://127.0.0.1:8000
NOTION3D_WEB_BASE=http://localhost:5173
NOTION3D_WEB_TURN=off          # off | bridge | gateway

# bridge — LLM 经 Cursor 云端
CURSOR_API_KEY=...

# gateway — 当前实现 Hermes；LLM 在 gateway 宿主
NOTION3D_WEB_TURN_GATEWAY_BASE=http://127.0.0.1:8642
HERMES_API_SERVER_KEY=...
```

Agent 宿主 MCP env：`NOTION3D_API_BASE` · `NOTION3D_WEB_BASE`（与 Engine 一致）。

Agent 接入：[agents/README.md](agents/README.md)
