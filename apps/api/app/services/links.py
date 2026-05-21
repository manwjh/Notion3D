"""Web workbench URLs for Agent ↔ human handoff."""

from __future__ import annotations

from app.config import settings


def web_base() -> str:
    return settings.web_base_url.rstrip("/")


def project_web_url(project_id: str) -> str:
    return f"{web_base()}/p/{project_id}"
