# Notion3D Agent 集成

Web 对话经 **Agent 适配层** 对接 Cursor SDK 或 Hermes Agent（Notion3D 无 LLM）。

- [docs/architecture.md](docs/architecture.md) — 架构与边界
- [docs/cad-backend-v2.md](docs/cad-backend-v2.md) — **ForgeCAD 后端（默认）**
- [docs/design-pipeline.md](docs/design-pipeline.md) — 分阶段设计流水线
- [docs/dev-modes.md](docs/dev-modes.md) — 本地运行模式

## 必须

1. `cd apps/forge-runner && npm install` — ForgeCAD 渲染依赖
2. `make dev AGENT=cursor_sdk` 或 `make dev AGENT=hermes`
3. 不要用裸 `make api` 代替完整 dev 栈

## 分阶段 Skills

| Skill | 阶段 |
|-------|------|
| `notion3d-openscad` | 总览 / orchestrator |
| `notion3d-intake` | 需求澄清 |
| `notion3d-plan` | 模板检索、plan |
| `notion3d-forge-author` | 写 ForgeCAD |
| `notion3d-mcp` | MCP 工具 |
| `notion3d-review` | 验收 |

## MCP Tools（主路径）

| Tool | 用途 |
|------|------|
| `notion3d_render_forge` | **提交 .forge.js → 装配渲染**（可选 `files_json` 多文件） |
| `notion3d_get_forge_sources` | 读取版本主脚本 + `src/` 子文件（改稿） |
| `notion3d_report_design_plan` | plan 阶段 |
| `notion3d_report_design_review` | review 阶段 |
| `notion3d_apply_template` | 应用 Forge 模板 |
| `notion3d_wait_job` | 等待 STL + parts |

Legacy：`notion3d_render_scad`（`templates/legacy/scad/`）

Web 预览：`装配`（STL 分件）| `Forge 实时`（内嵌 ForgeCAD Studio，`:5174`）
