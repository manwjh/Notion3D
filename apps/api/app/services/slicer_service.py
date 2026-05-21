import asyncio
import shutil
from pathlib import Path

from app.config import settings


class SlicerError(Exception):
    pass


def _candidate_bins() -> list[str]:
    if settings.orca_slicer_bin:
        return [settings.orca_slicer_bin]
    return [
        "orca-slicer",
        "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer",
        "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
        "bambu-studio",
    ]


def find_slicer_bin() -> str | None:
    for candidate in _candidate_bins():
        if Path(candidate).is_file():
            return candidate
        if shutil.which(candidate):
            return candidate
    return None


def slicer_available() -> bool:
    return find_slicer_bin() is not None


async def slice_stl_to_3mf(stl_path: Path, output_3mf: Path) -> Path:
    slicer = find_slicer_bin()
    if not slicer:
        raise SlicerError(
            "未找到切片软件。请安装 OrcaSlicer 或 Bambu Studio："
            " brew install --cask orcaslicer"
        )

    output_3mf.parent.mkdir(parents=True, exist_ok=True)

    # Orca/Bambu CLI: export sliced 3MF from STL
    proc = await asyncio.create_subprocess_exec(
        slicer,
        "--export-3mf",
        str(output_3mf),
        str(stl_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        detail = (stderr or stdout).decode(errors="replace").strip()
        raise SlicerError(detail or "切片失败")

    if not output_3mf.exists():
        raise SlicerError("切片完成但未生成 3MF 文件")

    return output_3mf
