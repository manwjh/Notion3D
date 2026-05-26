"""Web Turn sidecar configuration — interface names, not agent product names."""

from __future__ import annotations

WEB_TURN_OFF = "off"
WEB_TURN_BRIDGE = "bridge"
WEB_TURN_GATEWAY = "gateway"

WEB_TURN_VALUES = frozenset({WEB_TURN_OFF, WEB_TURN_BRIDGE, WEB_TURN_GATEWAY})

# Legacy dev env (NOTION3D_AGENT_PROVIDER, make dev AGENT=…) → interface id
_LEGACY_ALIASES: dict[str, str] = {
    "engine": WEB_TURN_OFF,
    "none": WEB_TURN_OFF,
    "off": WEB_TURN_OFF,
    "cursor_sdk": WEB_TURN_BRIDGE,
    "bridge": WEB_TURN_BRIDGE,
    "hermes": WEB_TURN_GATEWAY,
    "gateway": WEB_TURN_GATEWAY,
}


def normalize_web_turn(raw: str | None) -> str:
    if raw is None:
        return WEB_TURN_OFF
    key = str(raw).strip().lower()
    if not key:
        return WEB_TURN_OFF
    if key in WEB_TURN_VALUES:
        return key
    return _LEGACY_ALIASES.get(key, WEB_TURN_OFF)
