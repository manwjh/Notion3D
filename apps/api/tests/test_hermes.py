"""Hermes agent adapter tests."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.agents.base import AgentSessionHandle
from app.services.agents.hermes import HermesAdapter


def test_start_turn_posts_run():
    adapter = HermesAdapter()
    mock_resp = MagicMock()
    mock_resp.status_code = 202
    mock_resp.json.return_value = {"run_id": "run-1", "status": "started"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.agents.hermes.httpx.AsyncClient", return_value=mock_client):
        handle = asyncio.run(adapter.start_turn("proj-1", "20mm 立方体"))

    assert handle.provider == "hermes"
    assert handle.run_id == "run-1"
    assert handle.session_id == "notion3d-proj-1"
    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.await_args.kwargs
    assert call_kwargs["json"]["input"]
    assert call_kwargs["json"]["session_id"] == "notion3d-proj-1"


def test_collect_reply_returns_output():
    adapter = HermesAdapter()
    done_resp = MagicMock()
    done_resp.status_code = 200
    done_resp.json.return_value = {"status": "completed", "output": "模型已生成"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=done_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    handle = AgentSessionHandle(
        provider="hermes",
        session_id="notion3d-p1",
        run_id="run-1",
    )

    with patch("app.services.agents.hermes.httpx.AsyncClient", return_value=mock_client):
        reply = asyncio.run(adapter.collect_reply(handle))

    assert reply == "模型已生成"
