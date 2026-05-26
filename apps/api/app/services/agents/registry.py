"""Web Turn sidecar adapters — bridge + gateway."""

from __future__ import annotations

from app.config import settings
from app.services.agents.base import AgentAdapter
from app.services.agents.bridge_adapter import BridgeAdapter
from app.services.agents.gateway_adapter import GatewayAdapter
from app.services.web_turn_config import WEB_TURN_BRIDGE, WEB_TURN_GATEWAY, WEB_TURN_OFF, normalize_web_turn

_ADAPTERS: dict[str, AgentAdapter] = {
    WEB_TURN_BRIDGE: BridgeAdapter(),
    WEB_TURN_GATEWAY: GatewayAdapter(),
}

_ready_cache: dict[str, bool | None] = {aid: None for aid in _ADAPTERS}


async def _refresh_adapter_ready(adapter_id: str) -> bool:
    adapter = _ADAPTERS[adapter_id]
    info = await adapter.info_ready()
    _ready_cache[adapter_id] = info.ready
    return info.ready


def get_adapter(adapter_id: str) -> AgentAdapter | None:
    return _ADAPTERS.get(adapter_id)


async def refresh_provider_cache() -> None:
    for adapter_id in _ADAPTERS:
        await _refresh_adapter_ready(adapter_id)


def _configured_web_turn(preferred: str | None = None) -> str:
    raw = preferred if preferred is not None else settings.web_turn
    return normalize_web_turn(raw)


def resolve_adapter(preferred: str | None = None) -> AgentAdapter | None:
    choice = _configured_web_turn(preferred)
    if choice == WEB_TURN_OFF:
        return None
    if _ready_cache.get(choice) is not True:
        return None
    return _ADAPTERS.get(choice)


async def resolve_adapter_live(preferred: str | None = None) -> AgentAdapter | None:
    await refresh_provider_cache()
    adapter = resolve_adapter(preferred)
    if adapter:
        return adapter
    choice = _configured_web_turn(preferred)
    if choice == WEB_TURN_OFF or choice not in _ADAPTERS:
        return None
    if _ready_cache.get(choice) is False:
        return None
    await refresh_provider_cache()
    return resolve_adapter(preferred)


def bridge_ready() -> bool:
    choice = settings.normalized_web_turn
    if choice not in _ADAPTERS:
        return False
    return _ready_cache.get(choice) is True


def active_provider_id(preferred: str | None = None) -> str | None:
    adapter = resolve_adapter(preferred)
    return adapter.id if adapter else None
