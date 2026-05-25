"""Agent adapter registry — cursor_sdk + hermes."""

from __future__ import annotations

from app.config import settings
from app.services.agents.base import AgentAdapter, AgentProviderInfo
from app.services.agents.cursor_sdk import CursorSdkAdapter
from app.services.agents.hermes import HermesAdapter

_ADAPTERS: dict[str, AgentAdapter] = {
    "cursor_sdk": CursorSdkAdapter(),
    "hermes": HermesAdapter(),
}

_ready_cache: dict[str, bool | None] = {aid: None for aid in _ADAPTERS}


async def _refresh_adapter_ready(adapter_id: str) -> bool:
    adapter = _ADAPTERS[adapter_id]
    if hasattr(adapter, "info_ready"):
        info = await adapter.info_ready()
        ready = info.ready
    else:
        ready = adapter.info().ready
    _ready_cache[adapter_id] = ready
    return ready


def _adapter_ready_sync(adapter: AgentAdapter) -> bool:
    cached = _ready_cache.get(adapter.id)
    if cached is not None:
        return cached
    return adapter.info().ready


def get_adapter(provider_id: str) -> AgentAdapter | None:
    return _ADAPTERS.get(provider_id)


def list_provider_info() -> list[AgentProviderInfo]:
    providers: list[AgentProviderInfo] = []
    for adapter in _ADAPTERS.values():
        info = adapter.info()
        ready = _adapter_ready_sync(adapter)
        note = "" if ready else info.note
        providers.append(
            AgentProviderInfo(
                id=info.id,
                title=info.title,
                kind=info.kind,
                configured=info.configured,
                ready=ready,
                note=note,
            )
        )
    return providers


async def refresh_provider_cache() -> None:
    for adapter_id in _ADAPTERS:
        await _refresh_adapter_ready(adapter_id)


def resolve_adapter(preferred: str | None = None) -> AgentAdapter | None:
    choice = (preferred or settings.agent_provider or "cursor_sdk").strip().lower()
    if choice in ("engine", "none", "off"):
        return None
    adapter = _ADAPTERS.get(choice)
    if not adapter:
        return None
    if _ready_cache.get(choice) is not True:
        return None
    return adapter


async def resolve_adapter_live(preferred: str | None = None) -> AgentAdapter | None:
    """Refresh sidecar readiness and resolve adapter (Web turn entry)."""
    await refresh_provider_cache()
    adapter = resolve_adapter(preferred)
    if adapter:
        return adapter
    choice = (preferred or settings.agent_provider or "cursor_sdk").strip().lower()
    if choice in ("engine", "none", "off") or choice not in _ADAPTERS:
        return None
    if _ready_cache.get(choice) is False:
        return None
    await refresh_provider_cache()
    return resolve_adapter(preferred)


def bridge_ready() -> bool:
    """Sidecar / gateway for the active configured provider."""
    choice = (settings.agent_provider or "cursor_sdk").strip().lower()
    if choice == "hermes":
        return _ready_cache.get("hermes") is True
    return _ready_cache.get("cursor_sdk") is True


def active_provider_id(preferred: str | None = None) -> str | None:
    adapter = resolve_adapter(preferred)
    return adapter.id if adapter else None
