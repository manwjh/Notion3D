"""Agent adapter registry."""

from __future__ import annotations

from unittest.mock import patch

from app.services.agents.registry import _ready_cache, resolve_adapter


def test_engine_profile_disables_adapter():
    assert resolve_adapter("engine") is None
    assert resolve_adapter("none") is None


def test_unknown_provider_returns_none():
    assert resolve_adapter("openclaw") is None
    assert resolve_adapter("cursor_cloud") is None


def test_hermes_resolves_when_ready():
    _ready_cache["hermes"] = True
    try:
        adapter = resolve_adapter("hermes")
        assert adapter is not None
        assert adapter.id == "hermes"
    finally:
        _ready_cache["hermes"] = None


def test_hermes_not_ready_returns_none():
    _ready_cache["hermes"] = False
    try:
        assert resolve_adapter("hermes") is None
    finally:
        _ready_cache["hermes"] = None
