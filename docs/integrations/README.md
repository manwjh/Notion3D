# MCP 宿主配置

Agent 宿主通过 **notion3d-mcp** 调 Engine。Notion3D 不绑定具体 Agent 产品。

完整依赖表（含 LLM 归属）：[dependencies.md](../dependencies.md)

## 你需要什么

| 组件 | 谁提供 | 说明 |
|------|--------|------|
| **Engine + Web** | Notion3D | `make dev` |
| **notion3d-mcp** | 本仓库 | `make install` 或 `pip install -e apps/mcp-server` |
| **LLM** | **Agent 宿主** | OpenClaw 等宿主内配置；Notion3D 不含 LLM |

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
make install
# 或
cd apps/mcp-server && pip install -e .
which notion3d-mcp
```

## 宿主示例

| 宿主 | 配置文件 | 文档 |
|------|----------|------|
| OpenClaw | `~/.openclaw/openclaw.json` → `mcp.servers` | [openclaw.md](../agents/openclaw.md) |
| 其他 MCP 客户端 | 各宿主 MCP 配置 | 同上 env |

Web Turn（浏览器内对话）见 [agents/README.md](../agents/README.md) — Engine 经 sidecar 转发；sidecar 内部仍调 notion3d-mcp。

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
| `notion3d-mcp: command not found` | `make install` 或 `pip install -e apps/mcp-server` |
