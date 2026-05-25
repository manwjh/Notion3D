"""ForgeCAD rendering via apps/forge-runner."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.services.cad_types import CadError, RenderResult


@dataclass
class ForgeExportSummary:
    objects: int = 0
    parts: list[dict] = field(default_factory=list)


def forgecad_available() -> bool:
    if not shutil.which(settings.node_bin):
        return False
    runner = settings.forge_runner_dir / "export-parts.mjs"
    if not runner.exists():
        return False
    forge_pkg = settings.forge_runner_dir / "node_modules" / "forgecad" / "dist-cli" / "forgecad.js"
    return forge_pkg.exists() or shutil.which(settings.forgecad_bin) is not None


def _sanitize_forge(code: str) -> str:
    code = code.strip()
    fence = re.match(r"^```(?:forge|forgecad|javascript|js)?\s*\n?(.*?)```\s*$", code, re.DOTALL | re.IGNORECASE)
    if fence:
        code = fence.group(1).strip()
    return code


def prepare_forge(code: str) -> str:
    code = _sanitize_forge(code)
    if not code.strip():
        raise CadError("Forge 代码不能为空")
    return code


def static_forge_warnings(forge_code: str, extra_files: dict[str, str] | None = None) -> list[str]:
    warnings: list[str] = []
    if "import(" in forge_code and "http://" in forge_code:
        warnings.append("Forge 脚本包含远程 import，本地渲染可能失败")
    if "importAssembly(" in forge_code and not extra_files:
        warnings.append("主脚本使用 importAssembly 但未提供 files（应经 render_forge 传入 src/ 子文件）")
    if extra_files:
        for path in extra_files:
            if not path.endswith(".forge.js"):
                warnings.append(f"子文件 {path} 建议使用 .forge.js 扩展名")
    return warnings


def _normalize_src_rel(rel_path: str) -> str:
    rel = rel_path.strip().lstrip("/").replace("\\", "/")
    if not rel or ".." in rel.split("/"):
        raise CadError(f"非法子文件路径: {rel_path}")
    return rel


def list_src_files(out_dir: Path) -> list[str]:
    src_dir = out_dir / "src"
    if not src_dir.is_dir():
        return []
    paths: list[str] = []
    for path in src_dir.rglob("*"):
        if path.is_file():
            paths.append(path.relative_to(src_dir).as_posix())
    return sorted(paths)


def collect_src_files(out_dir: Path) -> dict[str, str]:
    src_dir = out_dir / "src"
    if not src_dir.is_dir():
        return {}
    files: dict[str, str] = {}
    for path in src_dir.rglob("*"):
        if path.is_file():
            rel = path.relative_to(src_dir).as_posix()
            files[rel] = path.read_text(encoding="utf-8")
    return files


def read_forge_sources(out_dir: Path) -> dict[str, str | dict[str, str]]:
    forge_path = out_dir / "model.forge.js"
    if not forge_path.exists():
        raise CadError("Forge 源码不存在")
    return {
        "forge_code": forge_path.read_text(encoding="utf-8"),
        "files": collect_src_files(out_dir),
    }


def read_src_file(out_dir: Path, rel_path: str) -> str:
    if ".." in rel_path.replace("\\", "/"):
        raise CadError(f"非法子文件路径: {rel_path}")
    rel = _normalize_src_rel(rel_path)
    src_root = (out_dir / "src").resolve()
    target = (src_root / rel).resolve()
    try:
        target.relative_to(src_root)
    except ValueError as exc:
        raise CadError(f"非法子文件路径: {rel_path}") from exc
    if not target.is_file():
        raise CadError(f"子文件不存在: {rel}")
    return target.read_text(encoding="utf-8")


def _write_forge_src_files(out_dir: Path, files: dict[str, str] | None) -> None:
    if not files:
        return
    for rel_path, content in files.items():
        rel = _normalize_src_rel(rel_path)
        if not rel.endswith(".forge.js"):
            raise CadError(f"子文件须为 .forge.js: {rel_path}")
        target = out_dir / "src" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(prepare_forge(content), encoding="utf-8")


async def render_forge(
    forge_code: str,
    out_dir: Path,
    *,
    project_id: str,
    version: int,
    extra_files: dict[str, str] | None = None,
) -> RenderResult:
    if not forgecad_available():
        raise CadError(
            "ForgeCAD 未就绪。请运行: cd apps/forge-runner && npm install"
        )

    forge_code = prepare_forge(forge_code)
    out_dir.mkdir(parents=True, exist_ok=True)
    forge_path = out_dir / "model.forge.js"
    forge_path.write_text(forge_code, encoding="utf-8")
    _write_forge_src_files(out_dir, extra_files)

    runner = settings.forge_runner_dir / "export-parts.mjs"
    cmd = [
        settings.node_bin,
        str(runner),
        str(forge_path),
        str(out_dir),
        "--project-id",
        project_id,
        "--version",
        str(version),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(settings.forge_runner_dir),
    )
    stdout, stderr = await proc.communicate()
    stdout_text = stdout.decode()
    stderr_text = stderr.decode()

    if proc.returncode != 0:
        detail = stderr_text or stdout_text or "ForgeCAD 渲染失败"
        raise CadError(detail.strip())

    stl_path = out_dir / "model.stl"
    if not stl_path.exists():
        raise CadError("ForgeCAD 未生成 model.stl")

    warnings = static_forge_warnings(forge_code, extra_files)
    summary = _parse_summary(stdout_text)
    if summary.objects == 0:
        warnings.append("ForgeCAD 导出未识别到命名部件，预览可能为单体网格")
    elif summary.objects < 3:
        warnings.append(f"ForgeCAD 导出 {summary.objects} 个部件，复杂装配建议 ≥3 个命名 part")

    return RenderResult(path=stl_path, warnings=warnings)


def _parse_summary(stdout_text: str) -> ForgeExportSummary:
    for line in reversed(stdout_text.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
            return ForgeExportSummary(
                objects=int(data.get("objects") or 0),
                parts=list(data.get("parts") or []),
            )
        except json.JSONDecodeError:
            continue
    return ForgeExportSummary()


async def validate_forge_render(
    forge_code: str,
    out_dir: Path,
    *,
    project_id: str = "template",
    version: int = 1,
) -> RenderResult:
    return await render_forge(
        forge_code,
        out_dir,
        project_id=project_id,
        version=version,
    )
