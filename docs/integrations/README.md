# MCP 宿主配置

Agent 宿主通过 **notion3d-mcp** 调 Engine。Notion3D 不绑定具体 Agent 产品。

Web 工作台：`make dev` → `http://localhost:5173`

## MCP 环境变量

```json
{
  "command": "notion3d-mcp",
  "env": {
    "NOTION3D_API_BASE": "http://127.0.0.1:8000",
    "NOTION3D_WEB_BASE": "http://localhost:5173"
  }
}
```

安装 MCP：

```bash
cd apps/mcp-server && pip install -e .
which notion3d-mcp
```

## 宿主示例

| 宿主 | 配置文件 | 文档 |
|------|----------|------|
| OpenClaw | `~/.openclaw/openclaw.json` → `mcp.servers` | [openclaw.md](../agents/openclaw.md) |
| 其他 MCP 客户端 | 各宿主 MCP 配置 | 同上 env |

Web Turn（浏览器内对话）见 [agents/README.md](../agents/README.md) — 不经 MCP 直连，但 sidecar 内部仍调 notion3d-mcp。

## 验证

```bash
make dev
# 在 Agent 宿主中：
notion3d_health()
```

## 故障排查

| 现象 | 检查 |
|------|------|
| MCP 不可用 | Engine `:8000`；`NOTION3D_API_BASE` |
| Web 链接打不开 | `NOTION3D_WEB_BASE` 与分享地址一致 |
