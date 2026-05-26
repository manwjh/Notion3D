# 本地开发模式

按 Agent 环境选择 profile：

```bash
make dev AGENT=cursor_sdk   # Web 对话 — Cursor SDK
make dev AGENT=hermes       # Web 对话 — Hermes
make dev AGENT=engine       # 无 Web 对话 — MCP / 手动 Forge
```

完整接入说明：[agents/README.md](agents/README.md)

## 进程与端口

| `AGENT` | 进程 | 端口 |
|---------|------|------|
| `cursor_sdk` | agent-bridge | 8787 |
| `cursor_sdk` / `hermes` / `engine` | API | 8000 |
| `cursor_sdk` / `hermes` / `engine` | Web | 5173 |
| `hermes` | hermes gateway | 8642 |
| （Forge 实时） | ForgeCAD Studio | 5174 |

## 启动后自检

```bash
AGENT=cursor_sdk bash scripts/check-dev-stack.sh
# 或 AGENT=hermes bash scripts/check-dev-stack.sh
```

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
# forgecad_available: true
```

## 局域网访问

`make dev` 启动 banner 会打印 `http://<本机 IP>:5173`。

分享项目链接时，在 `.env` 设置：

```env
NOTION3D_WEB_BASE=http://<IP>:5173
```

Web 设计助手 sidecar 在运行 `make dev` 的本机；局域网设备可正常使用对话。MCP env 中 `NOTION3D_WEB_BASE` 也需一致。详见 [agents/README.md](agents/README.md#局域网访问)。

## cursor_sdk

**前置**：`.env` 中 `CURSOR_API_KEY` · `make install`

见 [agents/README.md](agents/README.md#web--cursor_sdk)。

## hermes

见 [agents/hermes.md](agents/hermes.md)。

## engine

无 Web 对话。适用：

- OpenClaw / Cursor IDE / Claude Code 经 MCP 调 Engine
- Web 左栏手动改 ForgeCAD（参数 / 代码 / 部件精修）

见 [agents/README.md](agents/README.md#web--engine) · [integrations/README.md](integrations/README.md)

## 设计流水线

Agent：`report_design_plan` → `render_forge` → `wait_job` → `report_design_review`。

详见 [design-pipeline.md](design-pipeline.md) · [AGENTS.md](../AGENTS.md)。
