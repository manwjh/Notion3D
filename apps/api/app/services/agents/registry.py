"""Agent adapters — OpenClaw + Cursor SDK local + Cursor Cloud API (not IDE)."""

from __future__ import annotations

from app.config import settings
from app.services.agents.base import AgentAdapter, AgentProviderInfo
from app.services.agents.cursor_cloud import CursorCloudAdapter
from app.services.agents.cursor_sdk import CursorSdkAdapter
from app.services.agents.openclaw import OpenClawAdapter

_ADAPTERS: dict[str, AgentAdapter] = {
    "openclaw": OpenClawAdapter(),
    "cursor_sdk": CursorSdkAdapter(),
    "cursor_cloud": CursorCloudAdapter(),
}

# 有 CURSOR_API_KEY 时优先 SDK local（无需 tunnel），其次 OpenClaw，最后 Cloud API
_AUTO_ORDER = ("cursor_sdk", "openclaw", "cursor_cloud")

_sdk_adapter = _ADAPTERS["cursor_sdk"]
_sdk_ready_cache: bool | None = None


async def _cursor_sdk_ready() -> bool:
    global _sdk_ready_cache
    if isinstance(_sdk_adapter, CursorSdkAdapter):
        info = await _sdk_adapter.info_ready()
        _sdk_ready_cache = info.ready
        return info.ready
    return False


def _adapter_ready_sync(adapter: AgentAdapter) -> bool:
    if adapter.id == "cursor_sdk":
        if _sdk_ready_cache is not None:
            return _sdk_ready_cache
        return adapter.info().configured and bool(settings.cursor_sdk_bridge_base)
    return adapter.info().ready


def get_adapter(provider_id: str) -> AgentAdapter | None:
    return _ADAPTERS.get(provider_id)


def list_provider_info() -> list[AgentProviderInfo]:
    items: list[AgentProviderInfo] = []
    for adapter in _ADAPTERS.values():
        info = adapter.info()
        if adapter.id == "cursor_sdk":
            info = AgentProviderInfo(
                id=info.id,
                title=info.title,
                kind=info.kind,
                configured=info.configured,
                ready=_adapter_ready_sync(adapter),
                note=info.note,
            )
        items.append(info)
    return items


async def refresh_provider_cache() -> None:
    await _cursor_sdk_ready()


def resolve_adapter(preferred: str | None = None) -> AgentAdapter | None:
    choice = (preferred or settings.agent_provider or "auto").strip().lower()
    if choice != "auto":
        adapter = get_adapter(choice)
        return adapter if adapter and _adapter_ready_sync(adapter) else None
    for pid in _AUTO_ORDER:
        adapter = _ADAPTERS[pid]
        if _adapter_ready_sync(adapter):
            return adapter
    return None


def bridge_ready() -> bool:
    return _sdk_ready_cache is True


def active_provider_id(preferred: str | None = None) -> str | None:
    adapter = resolve_adapter(preferred)
    return adapter.id if adapter else None
