"""Unified design turn routing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from app.services.agents.base import AgentAdapterError, AgentSessionHandle


def test_turn_blocked_without_agent(client, project_id, monkeypatch):
    async def _no_adapter(_preferred=None):
        return None

    monkeypatch.setattr("app.services.turn_service.resolve_adapter_live", _no_adapter)

    res = client.post(f"/api/projects/{project_id}/turn", json={"content": "20mm 立方体"})
    assert res.status_code == 200
    body = res.json()
    assert body["routing"] == "blocked"
    assert body["reason"] == "no_agent"


def test_turn_routes_agent_when_adapter_ready(client, project_id, monkeypatch):
    handle = AgentSessionHandle(
        provider="fake",
        session_id="sess-1",
        run_id="run-1",
        external_url="https://example.com/run/1",
    )
    adapter = MagicMock()
    adapter.start_turn = AsyncMock(return_value=handle)

    async def _fake_adapter(_preferred=None):
        return adapter

    monkeypatch.setattr("app.services.turn_service.resolve_adapter_live", _fake_adapter)
    monkeypatch.setattr("app.services.turn_service.finish_agent_run", AsyncMock())

    res = client.post(f"/api/projects/{project_id}/turn", json={"content": "带铰链的盒子"})
    assert res.status_code == 200
    body = res.json()
    assert body["routing"] == "agent"
    assert body["turn_id"]
    assert body["assistant_message_id"] is None
    assert body["agent"]["provider"] == "fake"
    assert body["agent"]["run_id"] == "run-1"

    state = client.get(f"/api/projects/{project_id}/state").json()
    assistant_texts = [m["content"] for m in state["messages"] if m["role"] == "assistant"]
    assert not any("理解需求并建模" in t for t in assistant_texts)


def test_turn_blocked_on_agent_error(client, project_id, monkeypatch):
    adapter = MagicMock()
    adapter.start_turn = AsyncMock(side_effect=AgentAdapterError("bridge down"))

    async def _fake_adapter(_preferred=None):
        return adapter

    monkeypatch.setattr("app.services.turn_service.resolve_adapter_live", _fake_adapter)

    res = client.post(f"/api/projects/{project_id}/turn", json={"content": "复杂结构"})
    assert res.status_code == 200
    body = res.json()
    assert body["routing"] == "blocked"
    assert body["reason"] == "agent_error"


def test_project_state_requires_agent_mode(client, project_id, monkeypatch):
    async def _mark_unready():
        from app.services.agents.registry import _ready_cache

        _ready_cache["cursor_sdk"] = False
        _ready_cache["hermes"] = False

    monkeypatch.setattr(
        "app.services.capabilities.refresh_provider_cache",
        _mark_unready,
    )

    res = client.get(f"/api/projects/{project_id}/state")
    assert res.status_code == 200
    body = res.json()
    assert body["project"]["id"] == project_id
    assert body["capabilities"]["web_chat_mode"] == "setup_required"
    assert body["capabilities"]["assistant_ready"] is False
