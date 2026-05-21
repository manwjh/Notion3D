.PHONY: install api web mcp bridge dev stop

PYTHON ?= python3.11
WITH_ENV = bash scripts/with-env.sh

install:
	cd apps/api && $(PYTHON) -m pip install -e .
	cd apps/mcp-server && $(PYTHON) -m pip install -e .
	cd apps/agent-bridge && npm install
	cd apps/web && npm install

api:
	$(WITH_ENV) bash -c 'cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'

web:
	cd apps/web && npm run dev

mcp:
	$(WITH_ENV) bash -c 'cd apps/mcp-server && $(PYTHON) -m notion3d_mcp.server'

bridge:
	$(WITH_ENV) bash -c 'cd apps/agent-bridge && NOTION3D_REPO_ROOT="$(CURDIR)" npm start'

stop:
	@echo "Stopping Notion3D (:8000 API, :5173 Web)…"
	@-lsof -ti :8000 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "  API stopped" || true
	@-lsof -ti :5173 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :5173 | xargs kill -9 2>/dev/null && echo "  Web stopped" || true
	@-lsof -ti :8787 | xargs kill 2>/dev/null; sleep 0.2
	@-lsof -ti :8787 | xargs kill -9 2>/dev/null && echo "  Agent bridge stopped" || true

dev: stop
	@echo "Notion3D — API http://127.0.0.1:8000  Bridge http://127.0.0.1:8787  Web http://localhost:5173"
	@echo "Ctrl+C 停止全部；或另开终端执行 make stop"
	@sleep 0.3
	@trap 'kill 0' INT TERM; \
	( $(WITH_ENV) bash -c 'cd apps/agent-bridge && NOTION3D_REPO_ROOT="$(CURDIR)" npm start' ) & \
	( $(WITH_ENV) bash -c 'cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000' ) & \
	( cd apps/web && npm run dev ) & \
	wait
