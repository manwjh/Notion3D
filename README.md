# Notion3D — ForgeCAD 装配建模工作台

文本描述 → ForgeCAD 装配 → 部件预览 → 导出 STL。**引擎无 LLM**；智能由外部 Agent 经 MCP 接入。

- [docs/cad-backend-v2.md](docs/cad-backend-v2.md) — ForgeCAD 后端
- [docs/architecture.md](docs/architecture.md) — 架构

## 快速开始

```bash
make install                  # 含 apps/forge-runner npm install
make dev AGENT=cursor_sdk     # 需 .env 中 CURSOR_API_KEY
```

| `AGENT` | 用途 |
|---------|------|
| `cursor_sdk` | Web 对话 + Cursor SDK |
| `hermes` | Web 对话 + Hermes |
| `engine` | 仅 Engine/预览；Web 对话不可用 |

## Agent 工作流

```
1. notion3d_health()
2. notion3d_report_design_plan(...)
3. notion3d_render_forge(forge_code) 或 demo 时 notion3d_apply_template
4. notion3d_wait_job(...)
5. notion3d_report_design_review(...)
```

Legacy OpenSCAD：`notion3d_render_scad` + `scope=legacy` 模板。

## 目录

```
apps/
  api/            Engine
  web/            Vue 3 三栏工作台（StructurePanel · ViewportHost · ChatPanel）
  forge-runner/   ForgeCAD CLI 导出
  mcp-server/     notion3d-mcp
  agent-bridge/   Cursor SDK sidecar
templates/builtin/   Forge 模板
```

## MCP Tools（主路径）

| Tool | 说明 |
|------|------|
| `notion3d_render_forge` | 提交 .forge.js → STL + parts.json |
| `notion3d_apply_template` | 应用 Forge/legacy 模板 |
| `notion3d_wait_job` | 等待渲染 |
| `notion3d_render_scad` | Legacy OpenSCAD |

## 环境要求

- Python 3.11+、Node.js 20+
- `cd apps/forge-runner && npm install`（ForgeCAD）
- OpenSCAD 可选（legacy 路径）
- Web 对话：`CURSOR_API_KEY` 或 Hermes
