# Notion3D Agent 集成

Web 对话经 **Agent 适配层** 对接 Cursor SDK 或 Hermes Agent（Notion3D 无 LLM）。

- [docs/architecture.md](docs/architecture.md) — 架构与边界
- [docs/agents/README.md](docs/agents/README.md) — dev profile 总览
- [docs/agents/hermes.md](docs/agents/hermes.md) — Hermes 接入
- [docs/integrations/README.md](docs/integrations/README.md) — MCP 与引擎启动

## 必须

1. `make dev AGENT=cursor_sdk` 或 `make dev AGENT=hermes`
2. Cursor：`CURSOR_API_KEY`；Hermes：`~/.hermes` + notion3d MCP（见 hermes.md）
3. 不要用裸 `make api` 代替完整 dev 栈（Web 对话 sidecar 不会启动）

## MCP Tools（Agent 建模）

| Tool | 用途 |
|------|------|
| `notion3d_render_scad` | **首选**：提交 SCAD |
| `notion3d_list_templates` | 浏览内置/用户模板库 |
| `notion3d_apply_template` | 应用模板到项目 |
| `notion3d_save_template` | 从 version 另存为用户模板 |
| `notion3d_template` | 简单几何规则模板（无 LLM，dev only） |
| `notion3d_create_project` | 新建项目，含 `web_url` |
| `notion3d_wait_job` | 等待 STL |
