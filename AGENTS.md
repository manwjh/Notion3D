# Notion3D Agent 集成

Web 对话经 **Agent 适配层** 对接 Cursor SDK 或 Hermes（Notion3D 无 LLM）。

## 启动

```bash
cd apps/forge-runner && npm install   # 首次
make dev AGENT=<cursor_sdk|hermes|engine>   # 见 docs/agents/README.md
```

不要用裸 `make api` 代替完整 dev 栈。

## Skills（按序）

| Skill | 阶段 |
|-------|------|
| `notion3d-pipeline` | 总览 / orchestrator |
| `notion3d-intake` | 需求澄清 |
| `notion3d-plan` | 建模计划 |
| `notion3d-forge-author` | 写 ForgeCAD |
| `notion3d-mcp` | MCP 工具 |
| `notion3d-review` | 验收 |

正文：`.cursor/skills/*/SKILL.md`

## MCP 工作流

```
notion3d_health()
notion3d_report_design_plan(...)                    # from_scratch 或改上一版
notion3d_render_forge(forge_code, files_json=...)   # 多文件可选
notion3d_wait_job(...)
notion3d_report_design_review(...)
```

改稿：`notion3d_get_forge_sources(version)` → 修改 → `render_forge`  
演示：`notion3d_apply_template`（`hello-assembly` / `open-enclosure`）

## MCP Tools

| Tool | 用途 |
|------|------|
| `notion3d_render_forge` | 提交 `.forge.js` → STL + `parts.json` |
| `notion3d_get_forge_sources` | 读取主脚本 + `src/` 子文件 |
| `notion3d_report_design_plan` | plan 阶段 |
| `notion3d_report_design_review` | review 阶段 |
| `notion3d_apply_template` | 应用演示模板 |
| `notion3d_wait_job` | 等待渲染完成 |

Web 预览：`装配`（STL 分件）| `Forge 实时`（ForgeCAD Studio `:5174`）

## 延伸阅读

- [docs/agents/README.md](docs/agents/README.md) — 连接 Agent（cursor_sdk / hermes / OpenClaw）
- [docs/agents/openclaw.md](docs/agents/openclaw.md) — OpenClaw MCP
- [docs/architecture.md](docs/architecture.md) — 架构、Design Turn
- [docs/design-pipeline.md](docs/design-pipeline.md) — 流水线细节
- [docs/integrations/README.md](docs/integrations/README.md) — 外部 IDE MCP 配置
