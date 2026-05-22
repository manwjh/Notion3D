import asyncio
import re
import shutil
from pathlib import Path

from app.config import settings


class CadError(Exception):
    pass


def openscad_available() -> bool:
    return shutil.which(settings.openscad_bin) is not None


def _sanitize_scad(code: str) -> str:
    """Strip markdown fences and keep only OpenSCAD source."""
    code = code.strip()
    fence = re.match(r"^```(?:openscad|scad)?\s*\n?(.*?)```\s*$", code, re.DOTALL | re.IGNORECASE)
    if fence:
        code = fence.group(1).strip()
    if re.search(r"\b(import|include)\s*\(\s*['\"]?/", code):
        raise CadError("生成的 OpenSCAD 包含不允许的绝对路径引用")
    return code


def prompt_to_scad_heuristic(prompt: str) -> str:
    """Rule-based fallback when no LLM is configured."""
    p = prompt.lower()
    size = 20
    for token in re.findall(r"(\d+)\s*(?:mm|毫米)?", prompt):
        size = int(token)
        break

    if any(k in p for k in ("球", "sphere", "ball")):
        r = size / 2
        return f"sphere(r={r});"

    if any(k in p for k in ("圆柱", "cylinder", "柱")):
        h = size
        r = max(size / 4, 5)
        return f"cylinder(h={h}, r={r}, center=true);"

    if any(k in p for k in ("孔", "hole", "中空", "空心")):
        outer = size
        inner = max(size / 2, 5)
        return f"""difference() {{
  cube([{outer}, {outer}, {outer}], center=true);
  cylinder(h={outer + 2}, r={inner / 2}, center=true);
}}"""

    return f"cube([{size}, {size}, {size}], center=true);"


async def prompt_to_scad(
    prompt: str,
    existing_scad: str | None = None,
    *,
    user_prompt: str | None = None,
    region: str | None = None,
) -> str:
    # 智能 SCAD 由外部 Agent（Cursor / Claude Code / OpenClaw）生成并通过
    # 智能建模由 Agent 经 notion3d_render_scad 提交；cad_service 保留 NL→SCAD 供 job 管线复用。
    if existing_scad:
        return _apply_simple_edit(existing_scad, user_prompt or prompt, region=region)
    return prompt_to_scad_heuristic(user_prompt or prompt)


def _apply_simple_edit(scad: str, prompt: str, region: str | None = None) -> str:
    ctx = f"{region or ''} {prompt}"
    p = ctx.lower()

    if "孔" in ctx and any(k in p for k in ("大", "加大", "扩", "增大", "粗")):
        def enlarge_hole(m: re.Match[str]) -> str:
            r = round(float(m.group(2)) * 1.25, 2)
            return f"{m.group(1)}{r}"

        updated = re.sub(
            r"(cylinder\s*\([^)]*?\br\s*=\s*)([\d.]+)",
            enlarge_hole,
            scad,
            count=1,
        )
        if updated != scad:
            return updated

    if "孔" in ctx and any(k in p for k in ("小", "缩小", "细")):
        def shrink_hole(m: re.Match[str]) -> str:
            r = round(float(m.group(2)) * 0.8, 2)
            return f"{m.group(1)}{r}"

        updated = re.sub(
            r"(cylinder\s*\([^)]*?\br\s*=\s*)([\d.]+)",
            shrink_hole,
            scad,
            count=1,
        )
        if updated != scad:
            return updated

    # 仅当用户明确写了 Nmm 时才改立方体尺寸，避免误读点选坐标
    m = re.search(r"(\d+)\s*(?:mm|毫米)", prompt)
    if m and any(k in p for k in ("大", "小", "尺寸", "边长", "改为", "改成", "调整")):
        size = int(m.group(1))
        if "cube(" in scad:
            return re.sub(
                r"cube\(\[[^\]]+\]",
                f"cube([{size}, {size}, {size}]",
                scad,
                count=1,
            )

    return scad + f"\n// edit: {prompt}\n"


def _openscad_stderr_is_fatal(stderr_text: str) -> bool:
    lowered = stderr_text.lower()
    return "error:" in stderr_text or "mesh is not closed" in lowered


async def render_stl(scad_code: str, output_stl: Path) -> Path:
    if not openscad_available():
        raise CadError(
            f"未找到 OpenSCAD（{settings.openscad_bin}）。请安装: https://openscad.org/downloads.html"
        )

    scad_code = _sanitize_scad(scad_code)
    scad_path = output_stl.with_suffix(".scad")
    scad_path.write_text(scad_code, encoding="utf-8")

    proc = await asyncio.create_subprocess_exec(
        settings.openscad_bin,
        "-o",
        str(output_stl),
        str(scad_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    stderr_text = stderr.decode()
    if proc.returncode != 0:
        raise CadError(stderr_text or stdout.decode() or "OpenSCAD 渲染失败")
    if _openscad_stderr_is_fatal(stderr_text):
        raise CadError(stderr_text.strip() or "OpenSCAD 几何体无效（非封闭网格）")

    if not output_stl.exists():
        raise CadError("OpenSCAD 未生成 STL 文件")

    return output_stl


async def render_preview_png(scad_code: str, output_png: Path) -> Path | None:
    """Legacy PNG export — not used in Web preview pipeline (OpenSCAD --preview is low quality)."""
    if not openscad_available():
        return None
    scad_path = output_png.with_suffix(".scad")
    if not scad_path.exists():
        scad_path.write_text(_sanitize_scad(scad_code), encoding="utf-8")

    try:
        proc = await asyncio.create_subprocess_exec(
            settings.openscad_bin,
            "--preview",
            "-o",
            str(output_png),
            str(scad_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if output_png.exists():
            return output_png
    except Exception:
        pass
    return None
