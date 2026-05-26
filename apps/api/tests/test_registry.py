"""Gateway adapter registry tests."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.agents.base import AgentProviderInfo
from app.services.agents.registry import (
    _ready_cache,
    _ready_fail_streak,
    _ready_last_ok,
    _refresh_adapter_ready,
    resolve_adapter,
)


def test_off_profile_disables_adapter():
    assert resolve_adapter("engine") is None
    assert resolve_adapter("off") is None
    assert resolve_adapter("none") is None


def test_unknown_provider_returns_none():
    assert resolve_adapter("openclaw") is None


def test_gateway_resolves_when_ready():
    _ready_cache["gateway"] = True
    try:
        adapter = resolve_adapter("gateway")
        assert adapter is not None
        assert adapter.id == "gateway"
        adapter_legacy = resolve_adapter("hermes")
        assert adapter_legacy is not None
        assert adapter_legacy.id == "gateway"
    finally:
        _ready_cache["gateway"] = None


def test_gateway_not_ready_returns_none():
    _ready_cache["gateway"] = False
    try:
        assert resolve_adapter("gateway") is None
    finally:
        _ready_cache["gateway"] = None


def test_ready_cache_hysteresis_keeps_agent_after_transient_failure():
    _ready_cache["gateway"] = True
    _ready_fail_streak["gateway"] = 0
    _ready_last_ok["gateway"] = 1.0
    try:
        info = AgentProviderInfo(
            id="gateway",
            title="t",
            kind="http_sidecar",
            configured=True,
            ready=False,
            note="",
        )
        with patch(
            "app.services.agents.registry._ADAPTERS",
            {"gateway": type("A", (), {"info_ready": AsyncMock(return_value=info)})()},
        ):
            ready = asyncio.run(_refresh_adapter_ready("gateway"))
            assert ready is True
            assert _ready_cache["gateway"] is True
    finally:
        _ready_cache["gateway"] = None
        _ready_fail_streak["gateway"] = 0
        _ready_last_ok["gateway"] = 0.0
