"""Web chat mode and user-facing assistant labels."""

from __future__ import annotations

from app.services.agents import active_provider_id

_ASSISTANT_LABELS = {
    "cursor_sdk": "Cursor 设计助手",
    "openclaw": "OpenClaw 助手",
    "cursor_cloud": "Cursor 云端助手",
}


def assistant_label(provider_id: str | None) -> str | None:
    if not provider_id:
        return None
    return _ASSISTANT_LABELS.get(provider_id, "设计助手")


def web_chat_mode() -> str:
    return "agent" if active_provider_id() else "setup_required"


def capabilities() -> dict:
    active = active_provider_id()
    return {
        "web_chat_mode": web_chat_mode(),
        "assistant_label": assistant_label(active),
        "assistant_ready": bool(active),
    }
