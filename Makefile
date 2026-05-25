.PHONY: install api web mcp bridge dev dev-help stop test

PYTHON ?= python3.11
WITH_ENV = bash scripts/with-env.sh

install:
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
	@bash scripts/dev.sh 2>/dev/null || true
	@echo ""
	@echo "快捷: make dev-cursor  → AGENT=cursor_sdk"
	@echo "      make dev-hermes   → AGENT=hermes"

dev: stop
ifndef AGENT
	@$(MAKE) dev-help
	@exit 1
endif
	@chmod +x scripts/dev.sh
	@$(WITH_ENV) bash scripts/dev.sh "$(AGENT)"

dev-cursor:
	$(MAKE) dev AGENT=cursor_sdk

dev-hermes:
	$(MAKE) dev AGENT=hermes

dev-engine:
	$(MAKE) dev AGENT=engine

stop:
	@echo "Stopping Notion3D (:8000 API, :5173 Web, :8787 Bridge, :8642 Hermes)…"
	@-lsof -ti :8000 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "  API stopped" || true
	@-lsof -ti :5173 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :5173 | xargs kill -9 2>/dev/null && echo "  Web stopped" || true
	@-lsof -ti :8787 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8787 | xargs kill -9 2>/dev/null && echo "  Agent bridge stopped" || true
	@-lsof -ti :8642 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8642 | xargs kill -9 2>/dev/null && echo "  Hermes gateway stopped" || true

test:
	cd apps/api && $(PYTHON) -m pytest -q
	bash templates/scripts/validate-all.sh
