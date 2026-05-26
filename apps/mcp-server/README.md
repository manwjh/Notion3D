# notion3d-mcp

**接口 1：MCP** — Agent 宿主通过 `notion3d_*` tools 调 Notion3D Engine。

Requires workbench: `make dev`（不要用裸 `make api`）。

## 依赖

| 项 | 说明 |
|----|------|
| **Python** | 3.11+ |
| **Engine** | `make dev` → `:8000` |
| **LLM** | **Agent 宿主**提供；本包不含 LLM |
| **httpx, mcp** | 见 `pyproject.toml` |

完整归属表：[docs/dependencies.md](../../docs/dependencies.md)

## 安装

```bash
make install
# 或
cd apps/mcp-server && pip install -e .
which notion3d-mcp
```

## MCP env

```json
{
  "NOTION3D_API_BASE": "http://127.0.0.1:8000",
  "NOTION3D_WEB_BASE": "http://localhost:5173"
}
```

宿主示例：[docs/agents/openclaw.md](../../docs/agents/openclaw.md) · [docs/integrations/README.md](../../docs/integrations/README.md)

## Web Turn 说明

`WEB_TURN=bridge` 时，agent-bridge **也会 spawn 本 MCP**（建模仍走 `notion3d_*` tools）。因此 bridge 路径同样需要 `pip install -e apps/mcp-server`。
