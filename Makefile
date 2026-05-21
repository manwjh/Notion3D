.PHONY: install api web mcp dev

PYTHON ?= python3.11

install:
	cd apps/api && $(PYTHON) -m pip install -e .
	cd apps/mcp-server && $(PYTHON) -m pip install -e .
	cd apps/web && npm install

api:
	cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

mcp:
	cd apps/mcp-server && $(PYTHON) -m notion3d_mcp.server

dev:
	@echo "Run in two terminals (MCP optional for external agents):"
	@echo "  make api"
	@echo "  make web"
	@echo "Optional MCP for Cursor / Claude Code / OpenClaw:"
	@echo "  make mcp"
