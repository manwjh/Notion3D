# Agent 接入适配层

架构见 **[docs/architecture.md](../architecture.md)**。Notion3D **没有 LLM**。Web 对话经后端 **Agent 适配接口** 转发到外部 Agent。

## 重要区分

| | Cursor IDE | Cursor SDK / Cloud Agents API |
|---|------------|-------------------------------|
| 是什么 | 桌面编辑器 | **程序化**调 Agent（SDK 或 HTTP API） |
| Notion3D 是否集成 | **否** | **是** |
| 文档 | — | [TypeScript SDK](https://cursor.com/cn/docs/sdk/typescript) · [Cloud API](https://cursor.com/cn/docs/cloud-agent/api/endpoints) |

---

## 架构

```
Notion3D Web  ←→  Notion3D API  ←→  Agent Adapter
                                      ├── cursor_sdk（SDK local，推荐）
                                      ├── openclaw（本地 CLI）
                                      └── cursor_cloud（Cloud API + tunnel）
```

## 适配器

| ID | 类型 | 说明 |
|----|------|------|
| `cursor_sdk` | **local** | `@cursor/sdk` 本地运行时 → notion3d MCP → `127.0.0.1:8000`，**无需 tunnel** |
| `openclaw` | **local** | 本机 `openclaw agent --local` |
| `cursor_cloud` | **cloud** | `POST https://api.cursor.com/v1/agents`，需 `NOTION3D_PUBLIC_API_BASE` |

`NOTION3D_AGENT_PROVIDER=auto`：**cursor_sdk 优先**（有 Key + bridge 就绪），其次 openclaw，最后 cursor_cloud。

## Cursor SDK local（推荐）

只需 `CURSOR_API_KEY`，**不需要 tunnel**。

```env
CURSOR_API_KEY=crsr_...
NOTION3D_AGENT_PROVIDER=auto   # 或 cursor_sdk
```

```bash
make dev    # 同时启动 API + agent-bridge(:8787) + Web
# 或分开：
make api
make bridge
make web
```

Bridge 位于 `apps/agent-bridge/`，使用 [@cursor/sdk](https://cursor.com/cn/docs/sdk/typescript) `local` 运行时，内联 `notion3d` MCP 指向本机 API。

## OpenClaw

```env
NOTION3D_AGENT_PROVIDER=openclaw
```

## Cursor Cloud Agents API

仅当 Agent 必须在 Cursor 云端运行时使用；MCP 需公网访问 API。

```env
NOTION3D_AGENT_PROVIDER=cursor_cloud
CURSOR_API_KEY=crsr_...
NOTION3D_PUBLIC_API_BASE=https://你的-tunnel-地址
```

## Web 对话（用户视角）

Web 使用 **`POST /api/projects/{id}/turn`**，**必须**已连接外部 Agent：

| 条件 | 行为 |
|------|------|
| Agent 已连接 | 转发到外部 Agent → MCP 建模 |
| 未连接 | 返回 `blocked`（`reason: no_agent`） |

`/health` 的 `web_chat_mode`：`agent` | `setup_required`。

---

## 代码

```
apps/agent-bridge/          # @cursor/sdk local HTTP bridge
apps/api/app/services/agents/
  cursor_sdk.py
  openclaw.py
  cursor_cloud.py
  registry.py
```
