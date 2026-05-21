# Notion3D MCP Server

Unified Agent integration for **Cursor**, **Claude Code**, and **OpenClaw**.

## Install

```bash
cd apps/mcp-server
pip install -e .
```

Requires API running: `make api`

## Run

```bash
make mcp
# or
notion3d-mcp
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTION3D_API_BASE` | `http://127.0.0.1:8000` | Notion3D API base URL |
| `NOTION3D_MCP_POLL_MAX` | `600` | Max seconds for `notion3d_wait_job` |

## Tools

See `notion3d_mcp/server.py` — all tools prefixed with `notion3d_`.

Configuration examples: [docs/integrations/README.md](../../docs/integrations/README.md)
