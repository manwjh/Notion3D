# OpenClaw + MCP（示例）

OpenClaw 是 **MCP 路径**的宿主示例之一。经 **notion3d-mcp** 调 Engine；Web 工作台预览与精修。

← [Agent 接入总览](README.md)

## 前置

1. OpenClaw 已安装（`openclaw` 在 PATH）
2. OpenClaw 内已配置 LLM（Key 在 OpenClaw，不在 Notion3D）
3. `make install`

## 1. 启动工作台

```bash
make dev
```

API `:8000` · Web `:5173`（`WEB_TURN=off`，标准 MCP 栈）。

```bash
curl -s http://127.0.0.1:8000/health | grep forgecad_available
```

## 2. 安装 notion3d MCP

```bash
cd apps/mcp-server && pip install -e .
which notion3d-mcp
```

## 3. 配置 OpenClaw MCP

合并 [config/openclaw-notion3d-mcp.json](../../config/openclaw-notion3d-mcp.json) 到 `~/.openclaw/openclaw.json`：

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

重启 OpenClaw gateway。

## 4. 建模与预览

在 OpenClaw 调用 `notion3d_*` 工具。Web 预览：

```
http://localhost:5173/p/<project_id>
```

## 数据流

```
OpenClaw → notion3d-mcp → Engine :8000 → forge-runner → Web :5173
```

## 参考

- [OpenClaw MCP 文档](https://docs.openclaw.ai/cli/mcp)
- [Agent 接入总览](README.md)
