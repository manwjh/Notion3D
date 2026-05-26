# Agent 接入

Notion3D **不含 LLM**。建模智能由外部 Agent 提供；按你的环境选一条路径。

## 选路径

| 你的 Agent 环境 | 用途 | 文档 |
|-----------------|------|------|
| **Cursor SDK** | Web 设计助手对话 | [Web · cursor_sdk](#web--cursor_sdk) |
| **Hermes** | Web 设计助手对话 | [hermes.md](hermes.md) |
| **OpenClaw** | OpenClaw 经 MCP 建模 | [openclaw.md](openclaw.md) |
| **Cursor IDE / Claude Code** | IDE 内 Agent 经 MCP | [integrations/README.md](../integrations/README.md) |
| **无 Agent** | Web 预览、左栏改 Forge | [Web · engine](#web--engine) |

- **Web 设计助手**：`cursor_sdk` 与 `hermes` 二选一，`make dev AGENT=…` 启动对应 sidecar。
- **OpenClaw / IDE**：`notion3d-mcp` 调 Engine，不经 Web 对话；预览用 Web 工作台。

---

## Web · cursor_sdk

```env
# 项目根 .env
CURSOR_API_KEY=crsr_...
```

```bash
make install
make dev AGENT=cursor_sdk
```

打开 Web（`http://localhost:5173` 或局域网 `http://<本机 IP>:5173`）。设计助手显示 **已连接**。

```bash
curl -s http://127.0.0.1:8000/health | grep web_chat_mode
# "web_chat_mode":"agent"
```

Sidecar：`agent-bridge` `:8787`。

---

## Web · hermes

完整步骤见 **[hermes.md](hermes.md)**。

```bash
make install
make dev AGENT=hermes
```

Sidecar：`hermes gateway` `:8642`。

---

## Web · engine

```bash
make install
make dev AGENT=engine
```

启动 API `:8000` 与 Web `:5173`，无设计助手。左栏手动改 ForgeCAD，或配合 OpenClaw / IDE MCP 使用。

---

## 验证（Web 设计助手）

`/health` → `web_chat_mode`: `agent` | `setup_required`

OpenClaw / `engine` 路径下 `setup_required` 属正常（不经 Web 对话）。

Web 内 **助手** 面板可查看 `cursor_sdk` / `hermes` 就绪状态。

---

## 代码

```
scripts/dev.sh
apps/agent-bridge/              # cursor_sdk
apps/api/app/services/agents/   # cursor_sdk.py, hermes.py
apps/mcp-server/                # notion3d-mcp（OpenClaw / IDE）
```
