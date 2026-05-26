# Web Turn · bridge

**接口 2** 的一种 sidecar：`bridge` → agent-bridge `:8787` → notion3d-mcp → Engine。

← [Agent 接入总览](README.md)

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
curl -s http://127.0.0.1:8000/health | grep web_turn
# web_turn: bridge · web_chat_mode: agent（sidecar 就绪时）
```

Web 右侧「对话」可发送自然语言；UI 不暴露 bridge 细节。

## 数据流

```
Web POST /turn → Engine → bridge :8787 → Agent 运行时 + notion3d-mcp → Engine → Web 预览
```
