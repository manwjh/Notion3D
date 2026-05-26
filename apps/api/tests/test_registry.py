"""Gateway adapter registry tests."""

from __future__ import annotations

from app.services.agents.registry import _ready_cache, resolve_adapter


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
