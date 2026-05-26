"""Web chat availability — driven by WEB_TURN interface config."""

from __future__ import annotations

import time

from app.config import settings
from app.services.agents import active_provider_id, refresh_provider_cache
from app.services.agents.registry import _ADAPTERS, _ready_cache
from app.services.web_turn_config import WEB_TURN_OFF

_last_caps_refresh = 0.0
_CAPS_REFRESH_MIN_SEC = 5.0


def web_chat_mode() -> str:
    choice = settings.normalized_web_turn
    if choice == WEB_TURN_OFF:
        return "setup_required"
    adapter = _ADAPTERS.get(choice)
    if not adapter or not adapter.info().configured:
        return "setup_required"
    cached = _ready_cache.get(choice)
    if cached is False:
        return "setup_required"
    return "agent"


async def capabilities_async(*, agent_active: bool = False, force: bool = False) -> dict:
    global _last_caps_refresh
    now = time.monotonic()
    if (
        not force
        and agent_active
        and (now - _last_caps_refresh) < _CAPS_REFRESH_MIN_SEC
    ):
        return capabilities()
    await refresh_provider_cache()
    _last_caps_refresh = now
    return {
        "web_chat_mode": web_chat_mode(),
        "web_turn": settings.normalized_web_turn,
        "assistant_ready": bool(active_provider_id()),
    }


def capabilities() -> dict:
    return {
        "web_chat_mode": web_chat_mode(),
        "web_turn": settings.normalized_web_turn,
        "assistant_ready": bool(active_provider_id()),
    }
