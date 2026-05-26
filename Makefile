.PHONY: install api web mcp bridge dev dev-help stop test

PYTHON ?= python3.11
WITH_ENV = bash scripts/with-env.sh
WEB_TURN ?= off

install:
	@echo "Installing Notion3D stack (Python 3.11+, Node 20+) — see docs/dependencies.md"
	cd apps/api && $(PYTHON) -m pip install -e .
	cd apps/mcp-server && $(PYTHON) -m pip install -e .
	cd apps/agent-bridge && npm install
	cd apps/forge-runner && npm install
	cd apps/web && npm install

api:
	$(WITH_ENV) bash -c 'cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'

web:
	cd apps/web && npm run dev

mcp:
	$(WITH_ENV) bash -c 'cd apps/mcp-server && $(PYTHON) -m notion3d_mcp.server'

bridge:
	$(WITH_ENV) bash -c 'cd apps/agent-bridge && NOTION3D_REPO_ROOT="$(CURDIR)" npm start'

dev-help:
	@bash scripts/dev.sh --help

dev: stop
	@chmod +x scripts/dev.sh
	@$(WITH_ENV) WEB_TURN=$(WEB_TURN) bash scripts/dev.sh

dev-bridge:
	$(MAKE) dev WEB_TURN=bridge

dev-gateway:
	$(MAKE) dev WEB_TURN=gateway

# Legacy aliases
dev-cursor:
	$(MAKE) dev WEB_TURN=bridge

dev-hermes:
	$(MAKE) dev WEB_TURN=gateway

dev-engine:
	$(MAKE) dev WEB_TURN=off

stop:
	@echo "Stopping Notion3D (:8000 API, :5173 Web, :8787 Bridge, :8642 Gateway)…"
	@-lsof -ti :8000 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "  API stopped" || true
	@-lsof -ti :5173 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :5173 | xargs kill -9 2>/dev/null && echo "  Web stopped" || true
	@-lsof -ti :8787 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8787 | xargs kill -9 2>/dev/null && echo "  Web Turn bridge stopped" || true
	@-lsof -ti :8642 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8642 | xargs kill -9 2>/dev/null && echo "  Web Turn gateway stopped" || true

test:
	cd apps/api && $(PYTHON) -m pytest -q
	bash templates/scripts/validate-all.sh
