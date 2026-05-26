"""CAD backend — ForgeCAD only."""

from __future__ import annotations

from enum import Enum


class CadBackend(str, Enum):
    forgecad = "forgecad"


SOURCE_FILENAME = "model.forge.js"
