# OpenClaw 接入 Notion3D

OpenClaw 经 **notion3d-mcp** 调 Engine 建模。不经 Web 设计助手；用 Web 工作台预览 STL。

← [Agent 接入总览](README.md)

## 1. 启动 Engine 与 Web

```bash
make install
make dev AGENT=engine
```

启动 API `:8000` 与 Web `:5173`（无设计助手 sidecar）。

## 2. 配置 OpenClaw MCP

将 [config/openclaw-notion3d-mcp.json](../../config/openclaw-notion3d-mcp.json) 合并进 `~/.openclaw/openclaw.json` 的 `mcp.servers`：

```json
{
  "mcp": {
    "servers": {
      "notion3d": {
        "command": "notion3d-mcp",
        "env": {
          "NOTION3D_API_BASE": "http://127.0.0.1:8000",
          "NOTION3D_WEB_BASE": "http://localhost:5173"
        }
      }
    }
  }
}
```

或用 CLI：

```bash
openclaw mcp set notion3d '{"command":"notion3d-mcp","env":{"NOTION3D_API_BASE":"http://127.0.0.1:8000","NOTION3D_WEB_BASE":"http://localhost:5173"}}'
```

重启 OpenClaw gateway。

局域网预览时，将 `NOTION3D_WEB_BASE` 改为 `http://<本机 IP>:5173`。

## 3. 使用

在 OpenClaw 中调用 `notion3d_*` 工具（如 `notion3d_render_forge`、`notion3d_wait_job`）。

Web 预览：

```
http://localhost:5173/p/<project_id>
```

## 架构

```
OpenClaw Agent → notion3d-mcp → Engine :8000 → Web :5173 预览
```

LLM 与 API Key 在 OpenClaw 配置，不在 Notion3D。

## 参考

- [OpenClaw MCP](https://docs.openclaw.ai/cli/mcp)
- [AGENTS.md](../../AGENTS.md) — MCP 工具列表
