# notion3d-mcp

**接口 1：MCP** — Agent 宿主通过 `notion3d_*` tools 调 Notion3D Engine。

Requires workbench: `make dev`（不要用裸 `make api`）。

```bash
cd apps/mcp-server && pip install -e .
```

MCP env:

```json
{
  "NOTION3D_API_BASE": "http://127.0.0.1:8000",
  "NOTION3D_WEB_BASE": "http://localhost:5173"
}
```

宿主示例：[docs/agents/openclaw.md](../docs/agents/openclaw.md) · [docs/integrations/README.md](../docs/integrations/README.md)
