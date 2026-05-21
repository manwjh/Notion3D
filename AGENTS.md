# Notion3D Agent 集成

本仓库的 Agent（Cursor / Claude Code / OpenClaw）通过 **MCP Server `notion3d`** 操作建模流水线；Web 工作台用于预览与导出。

完整接入指南：[docs/integrations/README.md](docs/integrations/README.md)

## 必须

1. 启动 API：`make api`（http://127.0.0.1:8000）
2. 启动 Web（推荐）：`make web`（http://localhost:5173）
3. MCP 已配置：`.cursor/mcp.json` → `notion3d-mcp`
4. 遵循 Skill：`.cursor/skills/notion3d-openscad/SKILL.md`

## 职责划分

| 层 | 职责 |
|----|------|
| **Agent** | 理解需求、分类任务、生成 OpenSCAD；**API Key 由 Agent 平台管理** |
| **MCP** | `notion3d_*` 工具 → HTTP 调 FastAPI；返回 `web_url` |
| **API** | 渲染 OpenSCAD、Job/版本持久化；Web chat 仅规则模板 |
| **Web** | 预览、参数、导出；深链接 `/p/{project_id}` |

## Agent 操作规范

- **使用 MCP tools**（`notion3d_*`），不要手写 curl、不要臆造 STL
- **复杂建模优先 `notion3d_render_scad`**：Agent 自己写 SCAD 后提交渲染
- `notion3d_chat` 仅触发服务端规则模板（立方体、盒子等），不含 LLM
- 流程：`notion3d_health` → `notion3d_create_project` → `notion3d_render_scad` → `notion3d_wait_job` → **把 `web_url` 给用户**
- 任务是**异步**的；复杂模型 STL 可能 1–3 分钟

## Agent ↔ Web 衔接

```
notion3d_create_project / notion3d_wait_job 响应含 web_url
  → 例：http://localhost:5173/p/{project_id}
  → 用户在浏览器打开：3D 预览、调参、导出 STL
```

Agent 与 Web 共享 `data/projects/`，不直接通信。

## MCP Tools

| Tool | 用途 |
|------|------|
| `notion3d_health` | 检查 API / OpenSCAD |
| `notion3d_create_project` | 新建项目，含 `web_url` |
| `notion3d_render_scad` | **首选**：提交 SCAD |
| `notion3d_chat` | 简单 prompt → 规则模板 |
| `notion3d_wait_job` | 等待完成，含 `web_url` / `next_step` |
| `notion3d_list_versions` | 版本与 URL |
| `notion3d_resume_stl` | 断点续算 STL |
