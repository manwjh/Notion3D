# Notion3D Agent 集成

Web 对话经 **Agent 适配层** 对接外部 Agent（Notion3D 无 LLM）。

- [docs/architecture.md](docs/architecture.md) — 架构与边界
- [docs/agents/README.md](docs/agents/README.md) — Cursor SDK / OpenClaw / Cloud API
- [docs/integrations/README.md](docs/integrations/README.md) — MCP 与引擎启动

## 必须

1. `make dev` 启动 API + agent-bridge + Web
2. `.env` 配置 `CURSOR_API_KEY`（SDK local / Cloud API 共用）
3. `auto` 模式下优先 `cursor_sdk`（无需 tunnel）

## MCP Tools（Agent 建模）

| Tool | 用途 |
|------|------|
| `notion3d_render_scad` | **首选**：提交 SCAD |
| `notion3d_template` | 简单几何规则模板（无 LLM） |
| `notion3d_create_project` | 新建项目，含 `web_url` |
| `notion3d_wait_job` | 等待预览→STL |
