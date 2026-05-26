# 依赖与前置条件

Notion3D **引擎不含 LLM**。本文档说明：系统要求、仓库内模块依赖、各部署路径的**外部依赖归属**、环境变量索引。

部署场景速查仍见 [README.md § 建议部署](../README.md#建议部署)。

## 系统要求

| 要求 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | Engine、MCP server、pytest |
| **Node.js** | 20+（CI 基准） | Web、forge-runner、agent-bridge |
| **npm** | 随 Node | 安装上述 Node 子项目 |
| **git** | — | 拉取 `forgecad` npm 依赖（GitHub） |

可选系统工具：`curl`（自检）、`lsof`（`make stop`）。

## 一键安装（仓库内）

```bash
make install
```

等价于依次安装五个子项目：

| 子项目 | 目录 | 包管理 | 何时需要 |
|--------|------|--------|----------|
| **Engine API** | `apps/api` | `pip install -e .` | 始终 |
| **MCP server** | `apps/mcp-server` | `pip install -e .` | MCP 路径；**bridge 路径也必需**（sidecar 内 spawn） |
| **Forge runner** | `apps/forge-runner` | `npm install` | 始终（STL 渲染） |
| **Web 工作台** | `apps/web` | `npm install` | 始终 |
| **Web Turn bridge** | `apps/agent-bridge` | `npm install` | 仅 `WEB_TURN=bridge` |

> gateway sidecar **不在仓库内**：需自行安装 gateway CLI 到 PATH（当前实现为 **Hermes**）。

安装后复制配置：`cp .env.example .env`

## 仓库内模块依赖（包级）

真源：各目录 `pyproject.toml` / `package.json`。

| 模块 | 主要运行时依赖 | 说明 |
|------|----------------|------|
| `apps/api` | FastAPI, uvicorn, pydantic, httpx, aiofiles | Engine REST，无 LLM SDK |
| `apps/mcp-server` | `mcp`, httpx, starlette | 暴露 `notion3d_*` tools |
| `apps/forge-runner` | `forgecad` ← GitHub `mainline` + vendored `solver/pkg`（postinstall） | CLI + WASM 约束求解 |
| `apps/web` | Vue 3, Vite, Three.js, marked | 三栏工作台 |
| `apps/agent-bridge` | `@cursor/sdk` | 仅 bridge sidecar；调 Cursor 云端 Agent |

ForgeCAD 细节：[cad-backend-v2.md](cad-backend-v2.md)

## 外部依赖归属（按部署路径）

**LLM 从不在 Notion3D 进程内**；下表说明谁提供智能、谁提供 MCP、谁提供 sidecar。

| 路径 | Notion3D 进程 | 仓库内额外组件 | 部署层外部依赖 | LLM 由谁提供 |
|------|---------------|----------------|----------------|--------------|
| **A. MCP 建模** | API + Web + forge-runner | `notion3d-mcp`（装在 Agent 宿主或本机 PATH） | Agent 宿主 + 宿主侧 MCP 配置 | **Agent 宿主**（OpenClaw 等） |
| **B. Web Turn · bridge** | 同上 + agent-bridge `:8787` | `notion3d-mcp` + `@cursor/sdk` | `CURSOR_API_KEY` | **Cursor 云端**（经 API key） |
| **C. Web Turn · gateway** | 同上 + gateway `:8642` | Engine 侧 adapter | gateway CLI + API key + 宿主 MCP + LLM 配置 | **gateway 宿主**（当前 Hermes） |
| **D. 手动编辑** | API + Web + forge-runner | 无 | 无 | 无 |

### 路径 A — MCP（接口 1）

**Notion3D 负责**：`make dev` → Engine `:8000` + Web `:5173` + Forge 渲染。

**你另外需要**：

1. 本机或 Agent 宿主能执行 `notion3d-mcp`（`make install` 或 `pip install -e apps/mcp-server`）
2. **Agent 宿主**（OpenClaw、其他 MCP 客户端）及宿主内 **LLM 配置**
3. MCP env：`NOTION3D_API_BASE`、`NOTION3D_WEB_BASE`

文档：[agents/README.md](agents/README.md) · [integrations/README.md](integrations/README.md) · [agents/openclaw.md](agents/openclaw.md)

### 路径 B — bridge（接口 2）

**Notion3D 负责**：`make dev WEB_TURN=bridge` 启动 agent-bridge。

**Sidecar 链路**：`Engine → agent-bridge → @cursor/sdk Agent → notion3d-mcp → Engine`

**你另外需要**：

| 依赖 | 说明 |
|------|------|
| `CURSOR_API_KEY` | `.env` 中配置；供 bridge 调 Cursor 云端 LLM |
| `notion3d-mcp` | bridge 进程内 spawn；`make install` 已装 |
| `@cursor/sdk` | `apps/agent-bridge`；`make install` 已装 |

文档：[agents/web-turn-bridge.md](agents/web-turn-bridge.md)

### 路径 C — gateway（接口 2）

**Notion3D 负责**：`make dev WEB_TURN=gateway` 由 `dev.sh` 拉起 gateway HTTP API。

**Sidecar 链路**：`Engine → gateway HTTP Runs → Agent 运行时 → notion3d-mcp → Engine`

**你另外需要**：

| 依赖 | 说明 |
|------|------|
| **gateway CLI** | 默认 `hermes`，PATH 可执行；`NOTION3D_WEB_TURN_GATEWAY_BIN` 可改 |
| `HERMES_API_SERVER_KEY` | 与 gateway 宿主 `API_SERVER_KEY` 一致 |
| gateway 宿主 **LLM** | 在宿主配置（如 `~/.hermes/config.yaml`），不在 Notion3D |
| **notion3d MCP** | 合并 [config/hermes-notion3d-mcp.yaml](../config/hermes-notion3d-mcp.yaml) |

> **接口名 `gateway`，当前实现为 Hermes**（env 仍保留 `HERMES_*` 别名以兼容）。

文档：[agents/web-turn-gateway.md](agents/web-turn-gateway.md)

### 路径 D — 手动

仅需 **A 栈中 Notion3D 部分**（无 MCP、无 Web Turn、无 LLM）。Web 左栏改 Forge → `POST /render-forge`。

## ForgeCAD 与 Studio

| 组件 | 来源 | 说明 |
|------|------|------|
| **forgecad CLI** | `apps/forge-runner/node_modules/forgecad` | STL 导出；`/health` → `forgecad_available` |
| **ForgeCAD Studio** | 同上 npm 包内 | `make dev` 首次 forge-preview 时由 Engine 拉起 `:5174` |

无需单独安装 ForgeCAD 系统包；`make install` 通过 npm 拉取 GitHub 依赖。

## 本机与局域网

| 场景 | `NOTION3D_WEB_BASE` | 说明 |
|------|---------------------|------|
| **本机 Local** | `http://localhost:5173` | 默认；分享链接仅本机可开 |
| **局域网 LAN** | `http://<主机 IP>:5173` | 同事 / 手机同网段访问；MCP 异机时 API 也用主机 IP |

步骤、示意图、故障排查：[usage-network.md](usage-network.md)

## 环境变量索引

### 始终（工作台）

| 变量 | 默认 | 说明 |
|------|------|------|
| `NOTION3D_WEB_BASE` | `http://localhost:5173` | Web / 分享 / MCP 预览链接；**LAN 改为主机 IP** |
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | Engine；**MCP 异机时改为主机 IP** |
| `NOTION3D_CORS_ORIGINS` | localhost:5173 | LAN 访问时追加 `http://<IP>:5173` |

### Web Turn（可选）

| 变量 | 路径 | 说明 |
|------|------|------|
| `NOTION3D_WEB_TURN` | 全部 | `off` \| `bridge` \| `gateway` |
| `CURSOR_API_KEY` | bridge | Cursor 云端 API key |
| `NOTION3D_WEB_TURN_BRIDGE_BASE` | bridge | 默认 `http://127.0.0.1:8787` |
| `NOTION3D_WEB_TURN_GATEWAY_BIN` | gateway | 默认 `hermes` |
| `NOTION3D_WEB_TURN_GATEWAY_BASE` | gateway | 默认 `http://127.0.0.1:8642` |
| `HERMES_API_SERVER_KEY` | gateway | 与 gateway 宿主 API key 一致 |

完整模板：[.env.example](../.env.example)

## 自检

```bash
make install
make dev                    # 或 WEB_TURN=bridge|gateway
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
WEB_TURN=off bash scripts/check-dev-stack.sh
```

| `/health` 字段 | 期望 |
|----------------|------|
| `forgecad_available` | `true`（forge-runner 已装） |
| `web_turn` | 与 `.env` / `make dev` 一致 |
| `web_chat_mode` | `agent`（sidecar 就绪）或 `setup_required` |

bridge：`curl -s http://127.0.0.1:8787/health` → `api_ready: true`

gateway：`curl -s http://127.0.0.1:8642/health`

## 故障排查

| 现象 | 检查 |
|------|------|
| `forgecad_available: false` | `cd apps/forge-runner && npm install`（需存在 `solver/pkg/solver_bg.wasm`） |
| bridge 启动失败 | `CURSOR_API_KEY`；`python -c "import notion3d_mcp"` |
| gateway 启动失败 | `which hermes`；gateway 宿主 API key |
| MCP 工具失败 | Engine `:8000`；MCP env 与 `NOTION3D_WEB_BASE` 一致 |
| 分享链接同事打不开 | `NOTION3D_WEB_BASE` 用了 `localhost` | [usage-network.md](usage-network.md) |
| Web 对话不可用 | `web_turn_ready`；见 [agents/README.md](agents/README.md) |
