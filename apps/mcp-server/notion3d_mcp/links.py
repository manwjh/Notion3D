"""Workbench URLs for Agent tool responses."""

from __future__ import annotations

import os

WEB_BASE = os.environ.get("NOTION3D_WEB_BASE", "").rstrip("/")
_resolved_base: str | None = None


def set_web_base(base: str) -> None:
    global _resolved_base
    _resolved_base = base.rstrip("/")


def web_base() -> str:
    global _resolved_base
    if _resolved_base:
        return _resolved_base
    if WEB_BASE:
        return WEB_BASE
    return "http://localhost:5173"


def project_url(project_id: str) -> str:
    return f"{web_base()}/p/{project_id}"


def resolve_web_base_from_health(health: dict) -> None:
    base = health.get("web_base_url")
    if base:
        set_web_base(str(base))
