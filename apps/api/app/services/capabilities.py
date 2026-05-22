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
    active = active_provider_id()
    if active:
        return "agent"
    # Cache may be cold before first refresh; configured provider still counts as connectable.
    from app.config import settings

    choice = (settings.agent_provider or "cursor_sdk").strip().lower()
    if choice in ("engine", "none", "off"):
        return "setup_required"
    from app.services.agents.registry import _ready_cache, get_adapter

    adapter = get_adapter(choice)
    if adapter and adapter.info().configured and _ready_cache.get(choice) is not False:
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
