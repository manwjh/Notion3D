# Notion3D — 对话式 ForgeCAD 装配工作台

用自然语言描述需求，外部 Agent 写 ForgeCAD 脚本，Engine 渲染多部件装配，Web 三栏预览与导出。

**Notion3D 引擎不含 LLM**；建模智能由外部 Agent（Cursor SDK、Hermes、OpenClaw 等）经 MCP 或 Web 适配层接入。

## 特性

- **ForgeCAD 装配**：`.forge.js` 多部件、`importAssembly` 多文件 → STL + `parts.json` 分件预览
- **三栏工作台**：结构（部件树 / 文件 / 参数）· 3D 视口 · 设计助手
- **Forge 实时预览**：本机 ForgeCAD Studio（`:5174`），可调 `param()` 即时看几何
- **分阶段流水线**：intake → plan → author → render → review（MCP + Skills）

## 快速开始

```bash
make install
make dev AGENT=<cursor_sdk|hermes|engine>   # 按你的 Agent 环境选择，见 docs/agents/README.md
# → Web http://localhost:5173  ·  API http://127.0.0.1:8000
# 局域网：http://<本机 IP>:5173（见 make dev 启动输出）
```

| `AGENT` | 说明 |
|---------|------|
| `cursor_sdk` | Web 设计助手 — Cursor SDK |
| `hermes` | Web 设计助手 — Hermes |
| `engine` | 仅 Engine / 预览；OpenClaw、IDE MCP、手动改 Forge |

不要用裸 `make api` 代替完整 dev 栈。

## 目录

```
apps/api            Engine（render-forge、jobs、versions）
apps/web            Vue 3 工作台
apps/forge-runner   ForgeCAD CLI（npm）
apps/mcp-server     notion3d MCP
apps/agent-bridge   Cursor SDK sidecar
templates/builtin/  Forge 演示模板
.cursor/skills/     Agent 分阶段 Skills
docs/               架构与运行文档
```

## 文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](AGENTS.md) | Agent / Skills / MCP 速查 |
| [docs/README.md](docs/README.md) | 完整文档索引 |
| [docs/architecture.md](docs/architecture.md) | 架构与 API |
| [docs/cad-backend-v2.md](docs/cad-backend-v2.md) | ForgeCAD 安装与渲染 |
| [docs/dev-modes.md](docs/dev-modes.md) | 本地运行与自检 |
| [docs/agents/README.md](docs/agents/README.md) | 连接 Agent（cursor_sdk / hermes / OpenClaw） |
| [docs/agents/openclaw.md](docs/agents/openclaw.md) | OpenClaw + notion3d-mcp |

自检：`curl http://127.0.0.1:8000/health` → `forgecad_available: true`
