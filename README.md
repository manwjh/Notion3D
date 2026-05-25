# Notion3D — 对话式 ForgeCAD 装配工作台

用自然语言描述需求，外部 Agent 写 ForgeCAD 脚本，Engine 渲染多部件装配，Web 三栏预览与导出。

**Notion3D 引擎不含 LLM**；建模智能由 Cursor / Hermes 等 Agent 经 MCP 接入。

## 特性

- **ForgeCAD 主路径**：`.forge.js` 多部件装配、`importAssembly` 多文件、STL + `parts.json` 分件预览
- **三栏工作台**：左栏结构（部件树 / 文件 / 参数）· 中栏 3D 视口 · 右栏设计助手
- **Forge 实时预览**：内嵌 ForgeCAD Studio（`:5174`），可调 `param()` 即时看几何
- **分阶段设计流水线**：intake → plan → author → render → review（MCP + Skills）
- **Legacy OpenSCAD**：仅 `templates/legacy/scad/`，新功能不扩展 SCAD 模板库

## 快速开始

```bash
make install                  # Python deps + apps/forge-runner (ForgeCAD)
make dev AGENT=cursor_sdk     # 需 .env 中 CURSOR_API_KEY
# → Web http://localhost:5173  ·  API http://127.0.0.1:8000
```

| `AGENT` | 说明 |
|---------|------|
| `cursor_sdk` | Web 对话 + Cursor SDK（默认 `composer-2.5`） |
| `hermes` | Web 对话 + Hermes gateway |
| `engine` | 仅 Engine / 预览；Web 对话 sidecar 不启动 |

不要用裸 `make api` 代替完整 dev 栈（Web 对话需要 agent-bridge 或 Hermes）。

## Web 工作台

```
┌ 结构 ────────┬──── 3D 视口 ────┬─ 设计助手 ─┐
│ 部件树       │ 装配 / Forge实时 │ 对话       │
│ 文件列表     │ 点选修改         │ plan/review│
│ 参数 · 代码  │                  │            │
└──────────────┴──────────────────┴────────────┘
```

- **装配**：STL 分件树，点部件 → 助手预填修改意图
- **Forge 实时**：同步当前版本源码到 ForgeCAD Studio iframe
- **参数 / 代码**：左栏直接改 `param` 或 `.forge.js`（不经过助手）

## Agent 工作流（MCP）

```
notion3d_health()
notion3d_report_design_plan(...)          # 默认 from_scratch；改稿用 get_forge_sources
notion3d_render_forge(forge_code, files_json=...)   # 多文件可选
notion3d_wait_job(...)
notion3d_report_design_review(...)
```

| 场景 | 做法 |
|------|------|
| 新物件 | `from_scratch` → 写 `.forge.js` → `render_forge` |
| 改上一版 | `get_forge_sources(version)` → 修改 → `render_forge` |
| 演示冒烟 | `apply_template`（`hello-assembly` / `open-enclosure`） |

内置模板库**仅演示**，日常建模不依赖 `list_templates`。

Legacy：`notion3d_render_scad` + `templates/legacy/scad/`。

## 目录

```
apps/
  api/              FastAPI Engine（render-forge、jobs、versions）
  web/              Vue 3 工作台
  forge-runner/     ForgeCAD CLI 导出（model.stl + parts/）
  mcp-server/       notion3d-mcp
  agent-bridge/     Cursor SDK sidecar
templates/
  builtin/          Forge 演示模板（hello-assembly, open-enclosure）
  legacy/scad/      OpenSCAD 遗留模板
.cursor/skills/     Agent 分阶段 Skills
docs/               架构、流水线、dev 模式
```

## MCP Tools（常用）

| Tool | 说明 |
|------|------|
| `notion3d_render_forge` | 提交 `.forge.js` → STL + `parts.json`（可选 `files_json`） |
| `notion3d_get_forge_sources` | 读取版本主脚本 + `src/` 子文件 |
| `notion3d_report_design_plan` | 记录建模计划 |
| `notion3d_report_design_review` | 验收 / retry |
| `notion3d_wait_job` | 等待渲染完成 |
| `notion3d_apply_template` | 应用演示模板 |
| `notion3d_render_scad` | Legacy OpenSCAD |

## 环境要求

- Python 3.11+、Node.js 20+
- ForgeCAD：`cd apps/forge-runner && npm install`（`make install` 已包含）
- OpenSCAD：可选，仅 legacy 路径
- Web 对话：`CURSOR_API_KEY`（cursor_sdk）或 [Hermes 配置](docs/agents/hermes.md)

自检：`curl http://127.0.0.1:8000/health` → `forgecad_available: true`

## 文档

- [docs/architecture.md](docs/architecture.md) — 架构与边界
- [docs/cad-backend-v2.md](docs/cad-backend-v2.md) — ForgeCAD 后端与产物
- [docs/design-pipeline.md](docs/design-pipeline.md) — 分阶段设计流水线
- [docs/dev-modes.md](docs/dev-modes.md) — 本地运行与自检
- [AGENTS.md](AGENTS.md) — Agent / Skills / MCP 速查
