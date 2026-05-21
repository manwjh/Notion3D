# Notion3D — OpenSCAD 建模工作台

文本描述 → OpenSCAD 建模 → 预览图 → 3D 网格 → 导出 SCAD/STL。

## 如何接入你的 Agent 系统

Notion3D **不是** Agent。它是本地建模引擎 + Web 工作台；**你的 Agent**（Cursor / Claude Code / OpenClaw）通过 **MCP + Skill** 接入。

```
你的 Agent（自带 LLM + API Key）
  → MCP notion3d-mcp（notion3d_* tools）
  → FastAPI（渲染、Job、版本）
  → Web 工作台（预览、调参、导出）
```

**完整接入指南**：[docs/integrations/README.md](docs/integrations/README.md)

```bash
make install && make api && make web
# 在 Agent 平台配置 MCP，见 docs/integrations/
```

Agent 建模完成后返回 `web_url`（如 `http://localhost:5173/p/{id}`），用户在浏览器打开即可。

## 架构

```
apps/
  api/          FastAPI 后端（Job、版本、OpenSCAD 渲染）
  web/          Vue 3 + Vite 工作台（深链接 /p/:projectId）
  mcp-server/   MCP Server（Agent 统一工具层）
docs/
  integrations/ Agent 接入指南（Cursor / Claude Code / OpenClaw）
  skills/       跨平台 Skill 主文档
data/           项目产物（Agent 与 Web 共享）
```

| 层 | 职责 |
|----|------|
| Agent | 理解需求、写 OpenSCAD；API Key 在 Agent 平台 |
| MCP | `notion3d_*` tools → HTTP 调 API |
| API | OpenSCAD 渲染、持久化；Web chat 仅规则模板 |
| Web | 预览、参数、导出；不配置 LLM Key |

## 环境要求

- Python 3.11+、Node.js 18+
- OpenSCAD（`openscad` 在 PATH）
- Agent 平台配置 MCP（见 [docs/integrations/](docs/integrations/)）

## 快速开始

```bash
make install
make api    # :8000
make web    # :5173
```

## MCP Tools

| Tool | 说明 |
|------|------|
| `notion3d_health` | 检查 API / OpenSCAD |
| `notion3d_create_project` | 创建项目，返回 `web_url` |
| `notion3d_render_scad` | **首选**：Agent 提交 SCAD |
| `notion3d_chat` | 简单规则模板（无 LLM） |
| `notion3d_wait_job` | 等待预览→STL |

## 环境变量

`apps/api/.env`（可选）：

```env
NOTION3D_WEB_BASE=http://localhost:5173
NOTION3D_API_HOST=0.0.0.0
NOTION3D_API_PORT=8000
```

MCP：`NOTION3D_API_BASE=http://127.0.0.1:8000`
