"""CAD backend abstraction — ForgeCAD primary, OpenSCAD legacy."""

from __future__ import annotations

from enum import Enum


class CadBackend(str, Enum):
    forgecad = "forgecad"
    openscad_legacy = "openscad_legacy"


def normalize_backend(value: str | None) -> CadBackend:
    if not value:
        return CadBackend.forgecad
    try:
        return CadBackend(value)
    except ValueError:
        return CadBackend.forgecad


def source_filename(backend: CadBackend) -> str:
    return "model.forge.js" if backend == CadBackend.forgecad else "model.scad"


def source_field(backend: CadBackend) -> str:
    return "forge_code" if backend == CadBackend.forgecad else "scad_code"
