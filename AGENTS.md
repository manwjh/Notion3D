# Notion3D Agent 集成

Notion3D **不含 LLM**。建模智能由外部 Agent 经 MCP 或 Web 适配层接入。

## 客户端路径

| 路径 | 入口 | 典型 Agent |
|------|------|------------|
| **A. MCP** | `notion3d_*` tools | OpenClaw、Cursor IDE、Claude Code |
| **B. Web 对话** | `POST /turn` → Adapter | Cursor SDK、Hermes |
| **C. 手动编辑** | Web 左栏 | 无 Agent（参数 / 代码 / 部件精修） |

接入说明：[docs/agents/README.md](docs/agents/README.md)

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
| `notion3d_health` | 检查 Engine / ForgeCAD 就绪 |
| `notion3d_render_forge` | 提交 `.forge.js` → STL + `parts.json` |
| `notion3d_get_forge_sources` | 读取主脚本 + `src/` 子文件 |
| `notion3d_report_design_plan` | plan 阶段 |
| `notion3d_report_design_review` | review 阶段 |
| `notion3d_apply_template` | 应用演示模板 |
| `notion3d_wait_job` | 等待渲染完成 |

## Forge 编写约定（部件精修）

- 每个部件用 `const partId = ...`，`return` 中 `shape: partId`
- `return` 中 `name` 与 Web 部件树 label 一致
- 复杂部件拆到 `src/xxx.forge.js` + `importAssembly`
- 渲染后 `parts.json` 含 `source_ref`，Web 可点选跳转源码

## Web 预览

| 模式 | 说明 |
|------|------|
| **装配** | STL 分件 + 部件树 |
| **Forge 实时** | ForgeCAD Studio `:5174`，可调 `param()` |

## 延伸阅读

- [docs/agents/README.md](docs/agents/README.md) — 连接 Agent（cursor_sdk / hermes / OpenClaw / engine）
- [docs/agents/hermes.md](docs/agents/hermes.md) — Hermes Web 对话
- [docs/agents/openclaw.md](docs/agents/openclaw.md) — OpenClaw MCP
- [docs/architecture.md](docs/architecture.md) — 架构、Design Turn
- [docs/design-pipeline.md](docs/design-pipeline.md) — 流水线细节
- [docs/integrations/README.md](docs/integrations/README.md) — 外部 IDE MCP 配置
