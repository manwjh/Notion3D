# Notion3D 接入用户 Agent 系统

本文说明：**用户的 Agent 平台**（Cursor / Claude Code / OpenClaw）如何接入 **Notion3D 前后端**，以及 Agent 与 Web 工作台如何衔接。

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│  用户的 Agent 系统（自带 LLM + API Key）                  │
│  · Cursor / Claude Code / OpenClaw                      │
│  · Skill：建模规范与工作流                               │
│  · MCP 配置：启动 notion3d-mcp                             │
└───────────────────────┬─────────────────────────────────┘
                        │ stdio MCP（notion3d_* tools）
                        ▼
┌─────────────────────────────────────────────────────────┐
│  apps/mcp-server（适配层，无 LLM）                        │
│  · HTTP 调用 FastAPI                                     │
│  · 返回 web_url，供 Agent 交给用户打开工作台              │
└───────────────────────┬─────────────────────────────────┘
                        │ REST
                        ▼
┌─────────────────────────────────────────────────────────┐
│  apps/api（建模引擎）                                     │
│  · OpenSCAD 渲染、Job 队列、版本持久化                    │
│  · data/projects/ 共享状态                               │
└───────────────┬─────────────────────┬───────────────────┘
                │ REST                │ REST
                ▼                     ▼
         apps/web（工作台）      Agent 继续轮询 MCP
         预览 / 调参 / 导出
```

**要点**

- Agent **不**连 Web，两者都是 API 的客户端，通过 `data/` 共享项目。
- API Key 在 **Agent 平台**配置，Notion3D 不存 LLM Key。
- Agent 建完模型后，把 `web_url`（如 `http://localhost:5173/p/{project_id}`）给用户即可打开工作台。

---

## 第一步：运行 Notion3D 引擎

```bash
make install
make api          # 必须：http://127.0.0.1:8000
make web          # 推荐：http://localhost:5173
```

可选环境变量 `apps/api/.env`：

```env
NOTION3D_WEB_BASE=http://localhost:5173   # MCP 与 API 返回的工作台链接前缀
```

---

## 第二步：安装 MCP Server

```bash
cd apps/mcp-server && pip install -e .
# 安装后可用命令：notion3d-mcp
```

MCP 通过 HTTP 连接 API，环境变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | FastAPI 地址 |
| `NOTION3D_WEB_BASE` | 从 `/health` 读取 | 工作台 URL 前缀（可选覆盖） |

---

## 第三步：在 Agent 平台注册 MCP

### Cursor

`.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "notion3d": {
      "command": "notion3d-mcp",
      "env": {
        "NOTION3D_API_BASE": "http://127.0.0.1:8000",
        "NOTION3D_WEB_BASE": "http://localhost:5173"
      }
    }
  }
}
```

Skill：`.cursor/skills/notion3d-openscad/SKILL.md`（仓库已包含）

### Claude Code

`~/.claude/claude_desktop_config.json` 或项目 `.mcp.json`：

```json
{
  "mcpServers": {
    "notion3d": {
      "command": "notion3d-mcp",
      "env": {
        "NOTION3D_API_BASE": "http://127.0.0.1:8000"
      }
    }
  }
}
```

将 Skill 复制到 `.claude/skills/notion3d-openscad/`，或在 `CLAUDE.md` 中引用 `docs/skills/notion3d-openscad.md`。

### OpenClaw

`openclaw.json`：

```json
{
  "mcpServers": {
    "notion3d": {
      "command": "notion3d-mcp",
      "env": {
        "NOTION3D_API_BASE": "http://127.0.0.1:8000"
      }
    }
  }
}
```

在 system prompt 中引用 Skill 文档。

---

## 第四步：Agent 工作流（推荐）

```
1. notion3d_health()
2. notion3d_create_project(name="…")     → 得到 project_id、web_url
3. （Agent 自己写 OpenSCAD）
4. notion3d_render_scad(project_id, scad) → job_id
5. notion3d_wait_job(project_id, job_id)
6. 告诉用户：「请在浏览器打开 {web_url} 预览并导出 STL」
```

简单几何（立方体、盒子）可用 `notion3d_chat`（服务端规则模板，无 LLM）。

**异步**：预览先就绪，STL 可能需 1–3 分钟；务必 `notion3d_wait_job` 或轮询 `notion3d_get_job`。

---

## Agent ↔ Web 衔接

| 场景 | 行为 |
|------|------|
| Agent 创建项目 | API 落盘 → Web 15s 内自动刷新项目列表，或用户切回浏览器触发刷新 |
| Agent 返回链接 | `web_url` = `http://localhost:5173/p/{project_id}`，用户直达该项目 |
| 用户复制链接 | Web 顶栏「复制工作台链接」 |
| 用户微调 | Web 参数面板 / 快速调整（规则模板）；复杂改动回到 Agent |

Web **不是**第二个 Agent，而是 **可视化工作台**。

---

## MCP Tools 一览

| Tool | 用途 |
|------|------|
| `notion3d_health` | API + OpenSCAD 就绪 |
| `notion3d_create_project` | 新建项目，含 `web_url` |
| `notion3d_render_scad` | **首选**：提交 Agent 生成的 SCAD |
| `notion3d_chat` | 简单 NL → 规则模板 |
| `notion3d_wait_job` | 等待预览→STL |
| `notion3d_list_versions` | 版本与下载 URL |
| `notion3d_resume_stl` | 断点续算 STL |

完整规范见 [AGENTS.md](../../AGENTS.md) 与 [docs/skills/notion3d-openscad.md](../skills/notion3d-openscad.md)。

---

## 故障排查

| 现象 | 检查 |
|------|------|
| MCP tools 不可用 | `make api` 是否运行；`notion3d_health` |
| Web 看不到 Agent 项目 | 刷新页面；确认同一 `data/` 目录 |
| 链接打开「找不到项目」 | project_id 是否正确；API 是否同一实例 |
| OpenSCAD 失败 | `openscad` 是否在 PATH |
