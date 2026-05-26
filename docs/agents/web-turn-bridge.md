# Web Turn · bridge

**接口 2** 的一种 sidecar：`bridge` → agent-bridge `:8787` → `@cursor/sdk` Agent → notion3d-mcp → Engine。

← [Agent 接入总览](README.md) · 完整依赖表：[dependencies.md](../dependencies.md)

## Sidecar 依赖

| 组件 | 来源 | 说明 |
|------|------|------|
| **agent-bridge** | 仓库 `apps/agent-bridge` | `make install`；HTTP `:8787` |
| **@cursor/sdk** | agent-bridge `package.json` | 调 Cursor 云端 Agent 运行时 |
| **notion3d-mcp** | 仓库 `apps/mcp-server` | bridge 进程内 spawn；**必须** `pip install -e apps/mcp-server` |
| **LLM** | Cursor 云端 | `.env` 中 `CURSOR_API_KEY`；**不在 Notion3D Engine 内** |

`make dev WEB_TURN=bridge` 会预检 `CURSOR_API_KEY` 与 `import notion3d_mcp`。

## 部署

```env
NOTION3D_WEB_TURN=bridge
CURSOR_API_KEY=crsr_...
NOTION3D_WEB_TURN_BRIDGE_BASE=http://127.0.0.1:8787
```

```bash
make install
make dev WEB_TURN=bridge
# 或单独：make bridge（需 Engine + Web 已运行）
```

## 验证

```bash
curl -s http://127.0.0.1:8787/health
# api_ready: true · runtime: bridge
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
# web_turn: bridge · web_chat_mode: agent（sidecar 就绪时）
```

Web 右侧「对话」可发送自然语言；UI 不暴露 bridge 细节。

## 数据流

```
Web POST /turn → Engine → bridge :8787 → Cursor Agent + notion3d-mcp → Engine → Web 预览
```

## 故障排查

| 现象 | 检查 |
|------|------|
| `dev.sh` 报未安装 MCP | `cd apps/mcp-server && pip install -e .` |
| `api_ready: false` | `CURSOR_API_KEY` 有效；`curl bridge/health` |
| `web_chat_mode: setup_required` | bridge 进程是否运行；`NOTION3D_WEB_TURN_BRIDGE_BASE` |
