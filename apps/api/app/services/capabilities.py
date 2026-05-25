"""Web chat mode and user-facing assistant labels."""

from __future__ import annotations

from app.services.agents import active_provider_id, refresh_provider_cache


def assistant_label(provider_id: str | None) -> str | None:
    if provider_id == "cursor_sdk":
        return "Cursor 设计助手"
    if provider_id == "hermes":
        return "Hermes 设计助手"
    return None


def web_chat_mode() -> str:
    from app.config import settings
    from app.services.agents.registry import _ready_cache, get_adapter

    choice = (settings.agent_provider or "cursor_sdk").strip().lower()
    if choice in ("engine", "none", "off"):
        return "setup_required"
    adapter = get_adapter(choice)
    if not adapter or not adapter.info().configured:
        return "setup_required"
    if _ready_cache.get(choice) is True:
        return "agent"
    return "setup_required"


async def capabilities_async() -> dict:
    await refresh_provider_cache()
    active = active_provider_id()
    return {
        "web_chat_mode": web_chat_mode(),
        "assistant_label": assistant_label(active),
        "assistant_ready": bool(active),
    }


def capabilities() -> dict:
    active = active_provider_id()
    return {
        "web_chat_mode": web_chat_mode(),
        "assistant_label": assistant_label(active),
        "assistant_ready": bool(active),
    }
