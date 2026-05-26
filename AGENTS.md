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

## Skills（按序）

| Skill | 阶段 |
|-------|------|
| `notion3d-pipeline` | 总览 |
| `notion3d-intake` | 需求澄清 |
| `notion3d-plan` | 建模计划 |
| `notion3d-forge-author` | 写 ForgeCAD |
| `notion3d-mcp` | MCP 工具 |
| `notion3d-review` | 验收 |

## MCP 工作流

```
notion3d_health()
notion3d_report_design_plan(...)
notion3d_render_forge(forge_code, files_json=...)
notion3d_wait_job(...)
notion3d_report_design_review(...)
notion3d_get_forge_sources(...)
notion3d_apply_template(...)
```

主路径 tools：`notion3d_health` · `notion3d_report_design_plan` · `notion3d_render_forge` · `notion3d_wait_job` · `notion3d_report_design_review` · `notion3d_get_forge_sources` · `notion3d_apply_template`

**Web Turn / 状态**（`WEB_TURN=bridge|gateway` 或需读快照时）：`notion3d_get_project_state` · `notion3d_wait_agent`（等浏览器侧 Agent 跑完，`agent.active` → false）。Sidecar 示例：[docs/agents/web-turn-bridge.md](docs/agents/web-turn-bridge.md#mcp-辅助工具web-turn)

## 延伸阅读

- [docs/dependencies.md](docs/dependencies.md) — 依赖、LLM 归属、环境变量
- [docs/agents/README.md](docs/agents/README.md) — 接口与部署
- [docs/agents/openclaw.md](docs/agents/openclaw.md) — MCP 宿主示例（OpenClaw）
- [docs/architecture.md](docs/architecture.md) — 完整 API / MCP 表
