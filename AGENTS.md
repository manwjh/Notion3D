# Notion3D Agent 集成

Notion3D **不含 LLM**。建模智能由外部 Agent 经**技术接口**（MCP / Web Turn）接入。

## 客户端路径

| 路径 | 接口 | 用户入口 |
|------|------|----------|
| **A. MCP** | `notion3d_*` tools | Agent 宿主内对话；Web 工作台预览/编辑 |
| **B. Web 对话** | `POST /turn` → Web Turn sidecar | Web 右侧「对话」（部署可选） |
| **C. 手动编辑** | Web → `render-forge` | Web 左栏 |

接入说明：[docs/agents/README.md](docs/agents/README.md)

## 启动

```bash
make install                          # Python 3.11+ · Node 20+ · 见 docs/dependencies.md
make dev                              # MCP + 手动（默认）
make dev WEB_TURN=bridge              # + 浏览器内对话
```

不要用裸 `make api` 代替 `make dev`。

**依赖与 LLM 归属**：[docs/dependencies.md](docs/dependencies.md)

## 建模范式（render-first）

[docs/forge-modeling-guide.md](docs/forge-modeling-guide.md) — Agent **优先 render_forge**，用 `spatial_digest` / `validation_warnings`（可选改进）迭代；plan/review 为可选归档。

ForgeCAD 全量 API：`cd apps/forge-runner && npx forgecad skill install`

## Skills

| Skill | 阶段 |
|-------|------|
| `notion3d-pipeline` | 总览 |
| `notion3d-mcp` | MCP 工具与 render 循环 |

## MCP 主路径

```
notion3d_health()
notion3d_render_forge(forge_code, files_json=...)
notion3d_wait_job(...)
notion3d_get_forge_sources(...)   # 改稿
```

可选归档：`notion3d_report_design_plan` · `notion3d_report_design_review` · `notion3d_apply_template`

**Web Turn / 状态**：`notion3d_get_project_state` · `notion3d_wait_agent`

## 延伸阅读

- [docs/dependencies.md](docs/dependencies.md)
- [docs/agents/README.md](docs/agents/README.md)
- [docs/design-pipeline.md](docs/design-pipeline.md)
- [docs/architecture.md](docs/architecture.md)
