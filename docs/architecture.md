# Notion3D 架构

Notion3D = **OpenSCAD 渲染引擎** + **Web 工作台**。不含 LLM。

## 三层边界

```
┌─────────────────────────────────────────────────────────────┐
│  Engine（apps/api）— 无 LLM                                  │
│  项目 / Job / OpenSCAD 渲染 / 版本 / 文件持久化               │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   apps/web           apps/mcp-server    （可选）Web Agent 对话
   预览·导出·调参      Agent 工具层        → Adapter → 外部 LLM
```

| 层 | 目录 | 职责 |
|----|------|------|
| **Engine** | `apps/api` | CRUD、Job 队列、`render-scad`、模板 Job、版本 |
| **MCP** | `apps/mcp-server` | `notion3d_*` tools → HTTP 调 Engine |
| **Adapter** | `apps/api/.../agents` + `apps/agent-bridge` | 仅 Web 对话；转发到外部 Agent |
| **Web** | `apps/web` | 工作台 UI；不存 LLM Key |

## 两条客户端路径

### A. 外部 Agent（推荐）

```
Agent（自带 LLM）→ notion3d-mcp → Engine REST → data/projects/
                                              ↘ Web 预览（共享 data/）
```

主路径：`notion3d_render_scad` → `notion3d_wait_job` → 给用户 `web_url`。

简单几何（无 LLM）：`notion3d_template` → Engine 规则模板 Job。

### B. Web 对话

```
Web → POST /api/projects/{id}/turn
    → Adapter（cursor_sdk | openclaw | cursor_cloud）
    → 外部 Agent → notion3d MCP → Engine
```

**必须**配置 Agent，见 [docs/agents/README.md](agents/README.md)。

## 进程（本地开发）

```bash
make dev   # API :8000 + agent-bridge :8787 + Web :5173
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
| POST | `/api/projects/{id}/render-scad` | 提交 SCAD，创建渲染 Job |
| POST | `/api/projects/{id}/jobs/template` | 规则模板 NL→SCAD（无 LLM） |
| GET | `/api/projects/{id}/jobs/{job_id}` | Job 状态 |
| POST | `/api/projects/{id}/turn` | **Web 主入口**：转发到 Agent |
| GET | `/api/projects/{id}/agent/status` | Agent 运行中 + `active_job_id` |
| GET | `/api/projects/{id}/state` | 项目快照（消息 + Job + 能力） |

## MCP Tools

| Tool | 调用的 Engine |
|------|---------------|
| `notion3d_render_scad` | `POST .../render-scad` |
| `notion3d_template` | `POST .../jobs/template` |
| `notion3d_create_project` | `POST .../projects` |
| `notion3d_wait_job` | 轮询 `GET .../jobs/{id}` |

## 数据

```
data/
  projects/{id}/
    meta.json          # 含 agent_session_id、agent_run_pending
    messages.json      # Web 对话历史
    versions/{n}/
      model.scad
      model.stl
      preview.png
  jobs/{id}.json
```

Agent 与 Web 通过 **同一 `data/` 目录** 共享项目，不直连。

## 环境变量

根目录 `.env`：

```env
CURSOR_API_KEY=...              # cursor_sdk / cursor_cloud
NOTION3D_AGENT_PROVIDER=auto    # auto | cursor_sdk | openclaw | cursor_cloud
NOTION3D_WEB_BASE=http://localhost:5173
```

MCP（Agent 侧）：

```env
NOTION3D_API_BASE=http://127.0.0.1:8000
```
