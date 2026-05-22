# Notion3D — OpenSCAD 建模工作台

文本描述 → OpenSCAD → 预览 → 导出 STL。**引擎无 LLM**；智能由外部 Agent 经 MCP 接入。

**架构说明**：[docs/architecture.md](docs/architecture.md)

## 快速开始

```bash
make install
make dev AGENT=cursor_sdk   # 需 .env 中 CURSOR_API_KEY
# 或
make dev AGENT=hermes       # 需 hermes CLI + MCP 配置，见下方
```

| `AGENT` | 启动内容 | 用途 |
|---------|----------|------|
| `cursor_sdk` | bridge + API + Web | **Web 对话**（Cursor SDK） |
| `hermes` | hermes gateway + API + Web | **Web 对话**（Hermes Agent） |
| `engine` | API + Web | 仅引擎/预览；Web 对话不可用 |

```bash
make dev-help     # 查看全部 profile
make dev-cursor   # AGENT=cursor_sdk
make dev-hermes   # AGENT=hermes
```

---

## Agent 集成

Notion3D 与外部 Agent 有两种接法，按使用场景选择：

| 路径 | 适用场景 | Web 工作台对话 | 需要 sidecar |
|------|----------|----------------|--------------|
| **Adapter** | 用户在 Notion3D 网页里聊天建模 | ✅ | bridge 或 hermes gateway |
| **MCP** | 在 Claude Code / Codex / Cursor IDE 等终端或 IDE 里建模 | ❌ | 无（Agent 自带 LLM） |

```
路径 A — Web 对话（Adapter）
  Web → POST /turn → Adapter → Agent → notion3d MCP → Engine :8000

路径 B — 外部 Agent（MCP）
  Claude Code / Codex / … → stdio MCP → notion3d-mcp → Engine :8000
                                                      ↘ Web 预览 / 导出（共享 data/）
```

Agent 与 Web **不直连**，通过同一 Engine 与 `data/projects/` 共享项目。建模完成后把 **`web_url`**（形如 `http://localhost:5173/p/{id}`）给用户即可。

### 1. Cursor SDK（Web 对话，推荐）

在 Notion3D Web 里用自然语言描述模型，经本机 `@cursor/sdk` + agent-bridge 运行 Agent。

```env
# .env
CURSOR_API_KEY=crsr_...
```

```bash
make dev AGENT=cursor_sdk
```

- Sidecar：`apps/agent-bridge` → `http://127.0.0.1:8787`
- LLM Key：Cursor Dashboard → Integrations
- MCP：bridge 内自动 spawn `notion3d-mcp`

详见 [docs/agents/README.md](docs/agents/README.md)。

### 2. Hermes Agent（Web 对话）

在 Web 里对话，经本机 `hermes gateway` HTTP API 驱动 Agent。

```bash
# 1. 安装 Hermes CLI，合并 MCP 配置
#    config/hermes-notion3d-mcp.yaml → ~/.hermes/config.yaml

# 2. ~/.hermes/.env
#    API_SERVER_ENABLED=true
#    API_SERVER_KEY=change-me-local-dev

# 3. Notion3D .env
#    HERMES_API_SERVER_KEY=change-me-local-dev
```

```bash
make dev AGENT=hermes
```

- Sidecar：`hermes gateway` → `http://127.0.0.1:8642`
- LLM Key：在 Hermes（`~/.hermes`）配置，不在 Notion3D

详见 [docs/agents/hermes.md](docs/agents/hermes.md)。

### 3. Claude Code / Codex / Cursor IDE（MCP）

在终端或 IDE 里跟 Agent 说话，**不在 Notion3D Web 里聊天**。只需 Engine 运行 + 配置 MCP。

```bash
make install
make dev AGENT=engine    # 或 make api && make web
cd apps/mcp-server && pip install -e .
```

**Claude Code**（项目级 `.mcp.json` 或 CLI）：

```bash
claude mcp add --transport stdio notion3d \
  --env NOTION3D_API_BASE=http://127.0.0.1:8000 \
  --env NOTION3D_WEB_BASE=http://localhost:5173 \
  -- notion3d-mcp
```

**Codex**（`~/.codex/config.toml` 或 CLI）：

```bash
codex mcp add notion3d \
  --env NOTION3D_API_BASE=http://127.0.0.1:8000 \
  --env NOTION3D_WEB_BASE=http://localhost:5173 \
  -- notion3d-mcp
```

**Cursor IDE**：Settings → MCP，添加 stdio 服务器，`command`: `notion3d-mcp`，环境变量同上。

LLM Key 由各自平台管理；Notion3D 只提供 Engine 与 MCP 工具。

详见 [docs/integrations/README.md](docs/integrations/README.md)。

### Agent 工作流（通用）

无论哪种 Agent，建模流程一致：

```
1. notion3d_health()                          — 确认 Engine + OpenSCAD
2. notion3d_create_project(name="…")           — 获得 project_id、web_url
3. 生成 OpenSCAD → notion3d_render_scad(...)   — 复杂件首选
   或 notion3d_template(...)                   — 简单几何（无 LLM）
4. notion3d_wait_job(project_id, job_id)       — 等待预览 → STL（异步，1–3 分钟）
5. 回复用户：「请在浏览器打开 {web_url}」
```

### 集成对照

| Agent | Web 对话 | 启动命令 | LLM 配置位置 | 详细文档 |
|-------|----------|----------|--------------|----------|
| Cursor SDK | ✅ | `make dev-cursor` | `CURSOR_API_KEY` | [agents/README.md](docs/agents/README.md) |
| Hermes | ✅ | `make dev-hermes` | `~/.hermes` | [agents/hermes.md](docs/agents/hermes.md) |
| Claude Code | MCP | `make dev AGENT=engine` | Anthropic / Claude Code | [integrations/README.md](docs/integrations/README.md) |
| Codex | MCP | `make dev AGENT=engine` | OpenAI / Codex | [integrations/README.md](docs/integrations/README.md) |
| Cursor IDE | MCP | `make api` + Web | Cursor 账户 | [integrations/README.md](docs/integrations/README.md) |

---

## 目录

```
apps/
  api/            Engine — 渲染、Job、版本
  web/            Vue 3 工作台
  mcp-server/     Agent 工具层（notion3d-mcp）
  agent-bridge/   Cursor SDK local sidecar（AGENT=cursor_sdk）
config/           Hermes MCP 配置示例
data/             项目产物（Agent 与 Web 共享）
docs/
  architecture.md  架构与边界（主文档）
  agents/          Agent 适配层与 dev profile
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
- Web 对话：Cursor SDK 或 [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- MCP 集成：Claude Code、Codex、Cursor IDE 等（任选其一）
