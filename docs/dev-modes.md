# 本地开发模式

按 Agent 环境选择 profile：

```bash
make dev AGENT=cursor_sdk   # Web 对话 — Cursor SDK
make dev AGENT=hermes       # Web 对话 — Hermes
make dev AGENT=engine       # 无 Web 对话 — MCP / 手动 Forge
```

连接说明：[agents/README.md](agents/README.md)

启动后自检：

```bash
AGENT=cursor_sdk bash scripts/check-dev-stack.sh
# 或 AGENT=hermes bash scripts/check-dev-stack.sh
```

## 局域网访问

```bash
make dev AGENT=<你的 profile>
```

局域网内其他设备打开 `http://<运行 dev 机器的 IP>:5173`（启动 banner 会打印该地址）。

分享项目链接时，在 `.env` 设置：

```env
NOTION3D_WEB_BASE=http://<IP>:5173
```

Web 设计助手（cursor_sdk / hermes）的 sidecar 在运行 `make dev` 的本机；局域网设备可正常使用对话。

## cursor_sdk

| 进程 | 端口 | 职责 |
|------|------|------|
| agent-bridge | 8787 | `@cursor/sdk` + notion3d MCP |
| API | 8000 | Engine |
| Web | 5173 | 工作台 |

**前置**：`.env` 中 `CURSOR_API_KEY` · `make install`

## hermes

见 [agents/hermes.md](agents/hermes.md)。

## engine

无 Web 对话。左栏手动改 ForgeCAD，或 OpenClaw / IDE 经 MCP 调 Engine。

## 设计流水线

Agent：`report_design_plan` → `render_forge` → `wait_job` → `report_design_review`。

详见 [design-pipeline.md](design-pipeline.md)。
