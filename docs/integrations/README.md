# Notion3D 接入外部 Agent

完整架构见 **[docs/architecture.md](../architecture.md)**。本文是接入步骤。

## 架构（简图）

```
外部 Agent（LLM + MCP notion3d-mcp）
        │ stdio MCP
        ▼
apps/mcp-server  ──REST──►  apps/api（Engine）
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
              apps/web                 data/projects/
              预览 / 导出
```

Web 对话走 `POST /api/projects/{id}/turn` → Adapter → Agent → MCP → Engine（**必须**配置 Agent）。

---

## 第一步：运行 Engine

```bash
make install
make dev AGENT=cursor_sdk    # API :8000 + bridge :8787 + Web :5173
# 或：make api && make web
```

```env
NOTION3D_WEB_BASE=http://localhost:5173
```

---

## 第二步：安装 MCP

```bash
cd apps/mcp-server && pip install -e .
```

| 变量 | 默认 | 说明 |
|------|------|------|
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | Engine 地址 |

---

## 第三步：配置 Agent

| 方式 | 文档 |
|------|------|
| Cursor SDK local（Web 对话） | [docs/agents/README.md](../agents/README.md) |
| Hermes Agent（Web 对话） | [docs/agents/hermes.md](../agents/hermes.md) |
| Claude Code 等 | 自行配置 `notion3d-mcp` |

---

## 第四步：Agent 工作流

```
1. notion3d_health()
2. notion3d_create_project(name="…")     → project_id、web_url
3. （Agent 写 OpenSCAD）
4. notion3d_render_scad(project_id, scad) → job_id
5. notion3d_wait_job(project_id, job_id)
6. 告诉用户打开 {web_url}
```

简单几何（立方体、球）：`notion3d_template`（Engine 规则模板，**无 LLM**）。

**异步**：务必 `notion3d_wait_job` 或轮询 `notion3d_get_job`。

---

## MCP Tools

| Tool | Engine 端点 |
|------|-------------|
| `notion3d_render_scad` | `POST .../render-scad` |
| `notion3d_template` | `POST .../jobs/template` |
| `notion3d_create_project` | `POST .../projects` |
| `notion3d_wait_job` | 轮询 jobs |
| `notion3d_list_versions` | 版本列表 |
| `notion3d_resume_stl` | 断点续算 STL |

---

## 故障排查

| 现象 | 检查 |
|------|------|
| MCP 不可用 | `make api`；`notion3d_health` |
| Web 无 Agent 项目 | 刷新；同一 `data/` |
| Web 对话无响应 | `CURSOR_API_KEY` + bridge :8787 |
| OpenSCAD 失败 | `openscad` 在 PATH |
