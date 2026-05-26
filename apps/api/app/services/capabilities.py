"""Web chat availability — driven by WEB_TURN interface config."""

from __future__ import annotations

from app.config import settings
from app.services.agents import active_provider_id, refresh_provider_cache
from app.services.agents.registry import _ADAPTERS, _ready_cache
from app.services.web_turn_config import WEB_TURN_OFF


def web_chat_mode() -> str:
    choice = settings.normalized_web_turn
    if choice == WEB_TURN_OFF:
        return "setup_required"
    adapter = _ADAPTERS.get(choice)
    if not adapter or not adapter.info().configured:
        return "setup_required"
    if _ready_cache.get(choice) is True:
        return "agent"
    return "setup_required"


async def capabilities_async() -> dict:
    await refresh_provider_cache()
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
