"""CAD backend abstraction — ForgeCAD only."""

from __future__ import annotations

from enum import Enum


class CadBackend(str, Enum):
    forgecad = "forgecad"


def normalize_backend(value: str | None) -> CadBackend:
    if not value:
        return CadBackend.forgecad
    try:
        return CadBackend(value)
    except ValueError:
        return CadBackend.forgecad


def source_filename(_backend: CadBackend = CadBackend.forgecad) -> str:
    return "model.forge.js"


def source_field(_backend: CadBackend = CadBackend.forgecad) -> str:
    return "forge_code"
