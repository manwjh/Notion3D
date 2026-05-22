# Agent 接入适配层

架构见 **[docs/architecture.md](../architecture.md)**。Notion3D **没有 LLM**。Web 对话经后端 **Agent 适配接口** 转发到外部 Agent。

## 本地开发：必须指定集成环境

```bash
make dev AGENT=cursor_sdk    # Cursor SDK — bridge + API + Web
make dev AGENT=hermes        # Hermes Agent — gateway + API + Web
make dev AGENT=engine        # 仅 API + Web（无 Web 对话）
make dev-help
```

`make dev` **必须**带 `AGENT=`。脚本会校验前置条件、注入 `NOTION3D_AGENT_PROVIDER`，并按 profile 启动 sidecar（bridge 或 hermes gateway）。

| Profile | 进程 | Web 对话 |
|---------|------|----------|
| `cursor_sdk` | bridge:8787 + API:8000 + Web:5173 | ✅ Cursor SDK |
| `hermes` | hermes:8642 + API:8000 + Web:5173 | ✅ Hermes Agent |
| `engine` | API + Web | ❌ 仅 MCP / 外部 Agent 调 Engine |

---

## cursor_sdk（Web 对话）

```env
CURSOR_API_KEY=crsr_...
```

```bash
make dev AGENT=cursor_sdk
# 或: make dev-cursor
```

`@cursor/sdk` 经 agent-bridge 启动 Agent，挂载 notion3d MCP。

## hermes（Web 对话）

Hermes 使用本机 `hermes gateway` HTTP API + `~/.hermes/config.yaml` 中的 notion3d MCP。

完整步骤：**[docs/agents/hermes.md](hermes.md)**

```bash
make dev AGENT=hermes
# 或: make dev-hermes
```

## engine（无 Web 对话）

```bash
make dev AGENT=engine
```

---

## Web 对话

`POST /api/projects/{id}/turn` — 必须已连接 Agent（`engine` profile 除外）。

`/health` → `web_chat_mode`: `agent` | `setup_required`

---

## 代码

```
scripts/dev.sh
apps/agent-bridge/          # cursor_sdk
apps/api/app/services/agents/
  cursor_sdk.py
  hermes.py
  registry.py
```
