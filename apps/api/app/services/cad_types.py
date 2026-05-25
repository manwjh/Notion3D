from dataclasses import dataclass
from pathlib import Path


class CadError(Exception):
    pass


@dataclass
class RenderResult:
    path: Path
    warnings: list[str]
