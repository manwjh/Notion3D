# Notion3D — OpenSCAD 建模工作台

文本描述 → OpenSCAD → 预览 → 导出 STL。**引擎无 LLM**；智能由外部 Agent 经 MCP 接入。

**架构说明**：[docs/architecture.md](docs/architecture.md)

## 快速开始

```bash
make install
make dev    # API :8000 + agent-bridge :8787 + Web :5173
```

Web 对话需 `CURSOR_API_KEY`（Cursor SDK local，见 [docs/agents/README.md](docs/agents/README.md)）。

## 目录

```
apps/
  api/            Engine — 渲染、Job、版本
  web/            Vue 3 工作台
  mcp-server/     Agent 工具层（notion3d-mcp）
  agent-bridge/   Cursor SDK local sidecar（Web 对话用）
data/             项目产物（Agent 与 Web 共享）
docs/
  architecture.md  架构与边界（主文档）
  agents/          Agent 适配层配置
  integrations/    外部 Agent 接入指南
```

## MCP Tools

| Tool | 说明 |
|------|------|
| `notion3d_render_scad` | **首选**：Agent 提交 SCAD |
| `notion3d_template` | 简单几何规则模板（无 LLM） |
| `notion3d_create_project` | 新建项目，返回 `web_url` |
| `notion3d_wait_job` | 等待预览→STL |

## 环境要求

- Python 3.11+、Node.js 18+
- OpenSCAD（`openscad` 在 PATH）
