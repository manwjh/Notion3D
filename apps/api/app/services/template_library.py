"""Read-only template library — ForgeCAD builtin + legacy SCAD + user dir."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import settings
from app.services import cad_service, forgecad_service

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ASSIGN_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([\d.]+)\s*;\s*(?://.*)?$")
_FORGE_PARAM_RE = re.compile(
    r'param\s*\(\s*["\']([^"\']+)["\']\s*,\s*([\d.]+)',
)


class TemplateError(Exception):
    pass


def _scope_roots(scope: str) -> list[tuple[str, Path]]:
    if scope == "builtin":
        return [("builtin", settings.templates_dir / "builtin")]
    if scope == "user":
        return [("user", settings.user_templates_dir)]
    if scope == "legacy":
        return [("legacy", settings.templates_dir / "legacy" / "scad" / "builtin")]
    return [
        ("builtin", settings.templates_dir / "builtin"),
        ("user", settings.user_templates_dir),
        ("legacy", settings.templates_dir / "legacy" / "scad" / "builtin"),
    ]


def _detect_format(entry_dir: Path, meta: dict) -> str:
    fmt = meta.get("format")
    if fmt in ("forge", "scad"):
        return fmt
    if (entry_dir / "model.forge.js").exists():
        return "forge"
    if (entry_dir / "model.scad").exists():
        return "scad"
    raise TemplateError(f"模板缺少 model.forge.js 或 model.scad: {entry_dir.name}")


def _load_meta(entry_dir: Path) -> dict:
    meta_path = entry_dir / "meta.json"
    if not meta_path.exists():
        raise TemplateError(f"缺少 meta.json: {entry_dir.name}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.setdefault("id", entry_dir.name)
    meta["format"] = _detect_format(entry_dir, meta)
    return meta


def _entry_matches(meta: dict, *, tag: str | None, category: str | None) -> bool:
    if category and meta.get("category") != category:
        return False
    if tag:
        tags = [t.lower() for t in meta.get("tags") or []]
        if tag.lower() not in tags:
            return False
    return True


def _resolve_entry(template_id: str) -> tuple[str, Path, dict]:
    for scope, root in _scope_roots("all"):
        entry_dir = root / template_id
        if not entry_dir.is_dir():
            continue
        meta = _load_meta(entry_dir)
        meta["scope"] = scope
        return scope, entry_dir, meta
    raise TemplateError(f"模板不存在: {template_id}")


def list_templates(
    *,
    tag: str | None = None,
    category: str | None = None,
    scope: str = "all",
) -> list[dict]:
    items: list[dict] = []
    for scope_name, root in _scope_roots(scope):
        if not root.exists():
            continue
        for entry_dir in sorted(root.iterdir()):
            if not entry_dir.is_dir():
                continue
            try:
                meta = _load_meta(entry_dir)
            except TemplateError:
                continue
            if not _entry_matches(meta, tag=tag, category=category):
                continue
            items.append(
                {
                    "id": meta["id"],
                    "title": meta.get("title", meta["id"]),
                    "description": meta.get("description"),
                    "tags": meta.get("tags") or [],
                    "category": meta.get("category"),
                    "license": meta.get("license"),
                    "source": meta.get("source", scope_name),
                    "scope": scope_name,
                    "format": meta.get("format", "forge"),
                    "params": meta.get("params") or [],
                }
            )
    return items


def get_template(template_id: str) -> dict:
    scope, entry_dir, meta = _resolve_entry(template_id)
    fmt = meta.get("format", "forge")
    result = {
        "id": meta["id"],
        "title": meta.get("title", meta["id"]),
        "description": meta.get("description"),
        "tags": meta.get("tags") or [],
        "category": meta.get("category"),
        "license": meta.get("license"),
        "source": meta.get("source", scope),
        "scope": scope,
        "format": fmt,
        "params": meta.get("params") or [],
        "scad_code": None,
        "forge_code": None,
    }
    if fmt == "forge":
        forge_path = entry_dir / "model.forge.js"
        if not forge_path.exists():
            raise TemplateError(f"模板缺少 model.forge.js: {template_id}")
        forge_code = forge_path.read_text(encoding="utf-8")
        forgecad_service.prepare_forge(forge_code)
        result["forge_code"] = forge_code
    else:
        scad_path = entry_dir / "model.scad"
        if not scad_path.exists():
            raise TemplateError(f"模板缺少 model.scad: {template_id}")
        scad_code = scad_path.read_text(encoding="utf-8")
        cad_service._sanitize_scad(scad_code)
        result["scad_code"] = scad_code
    return result


def apply_param_overrides_scad(scad_code: str, params: dict[str, float]) -> str:
    if not params:
        return scad_code
    lines = scad_code.split("\n")
    for name, value in params.items():
        line_re = re.compile(rf"^(\s*{re.escape(name)}\s*=\s*)([\d.]+)")
        replaced = False
        for i, line in enumerate(lines):
            if line_re.match(line):
                lines[i] = line_re.sub(rf"\g<1>{value}", line, count=1)
                replaced = True
                break
        if not replaced:
            raise TemplateError(f"SCAD 中未找到参数: {name}")
    return "\n".join(lines)


def apply_param_overrides_forge(forge_code: str, params: dict[str, float]) -> str:
    if not params:
        return forge_code
    updated = forge_code
    for name, value in params.items():
        pattern = re.compile(
            rf'(param\s*\(\s*["\']{re.escape(name)}["\']\s*,\s*)([\d.]+)',
        )
        if not pattern.search(updated):
            raise TemplateError(f"Forge 脚本中未找到参数: {name}")
        updated = pattern.sub(rf"\g<1>{value}", updated, count=1)
    return updated


def prepare_source(template_id: str, params: dict[str, float] | None = None) -> tuple[dict, str, str]:
    detail = get_template(template_id)
    fmt = detail["format"]
    if fmt == "forge":
        code = detail["forge_code"] or ""
        if params:
            code = apply_param_overrides_forge(code, params)
        code = forgecad_service.prepare_forge(code)
        return detail, code, "forge"
    code = detail["scad_code"] or ""
    if params:
        code = apply_param_overrides_scad(code, params)
    code = cad_service._sanitize_scad(code)
    return detail, code, "scad"


def prepare_scad(template_id: str, params: dict[str, float] | None = None) -> tuple[dict, str]:
    detail, code, fmt = prepare_source(template_id, params)
    if fmt != "scad":
        raise TemplateError(f"模板 {template_id} 是 ForgeCAD 格式，请使用 prepare_forge")
    return detail, code


def prepare_forge(template_id: str, params: dict[str, float] | None = None) -> tuple[dict, str]:
    detail, code, fmt = prepare_source(template_id, params)
    if fmt != "forge":
        raise TemplateError(f"模板 {template_id} 是 OpenSCAD 格式，请使用 prepare_scad")
    return detail, code


def save_user_template(
    *,
    template_id: str,
    title: str,
    scad_code: str | None = None,
    forge_code: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
    params: list[dict] | None = None,
    derived_from: dict | None = None,
) -> dict:
    if not _SLUG_RE.match(template_id):
        raise TemplateError("模板 id 须为小写字母、数字与连字符")
    if (settings.user_templates_dir / template_id).exists():
        raise TemplateError(f"模板 id 已存在: {template_id}")

    fmt = "forge" if forge_code else "scad"
    entry_dir = settings.user_templates_dir / template_id
    entry_dir.mkdir(parents=True, exist_ok=False)

    if fmt == "forge":
        forge_code = forgecad_service.prepare_forge(forge_code or "")
        (entry_dir / "model.forge.js").write_text(forge_code, encoding="utf-8")
        if params is None:
            params = _infer_forge_params(forge_code)
    else:
        scad_code = cad_service.prepare_scad(scad_code or "")
        (entry_dir / "model.scad").write_text(scad_code, encoding="utf-8")
        if params is None:
            params = _infer_scad_params(scad_code)

    meta = {
        "id": template_id,
        "title": title,
        "description": description,
        "tags": tags or [],
        "category": category,
        "license": "user",
        "source": "user",
        "format": fmt,
        "params": params,
    }
    if derived_from:
        meta["derived_from"] = derived_from
    (entry_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    meta["scope"] = "user"
    return meta


async def save_user_template_validated(
    *,
    template_id: str,
    title: str,
    scad_code: str,
    description: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
    params: list[dict] | None = None,
    derived_from: dict | None = None,
) -> dict:
    import tempfile

    scad_code = cad_service.prepare_scad(scad_code)
    with tempfile.TemporaryDirectory(prefix="notion3d-template-") as tmp:
        result = await cad_service.validate_scad_render(
            scad_code,
            Path(tmp) / "model.stl",
        )

    meta = save_user_template(
        template_id=template_id,
        title=title,
        scad_code=scad_code,
        description=description,
        tags=tags,
        category=category,
        params=params,
        derived_from=derived_from,
    )
    if result.warnings:
        meta_path = settings.user_templates_dir / template_id / "meta.json"
        stored = json.loads(meta_path.read_text(encoding="utf-8"))
        stored["validation_warnings"] = result.warnings
        meta_path.write_text(
            json.dumps(stored, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        meta["validation_warnings"] = result.warnings
    return meta


async def save_user_forge_template_validated(
    *,
    template_id: str,
    title: str,
    forge_code: str,
    description: str | None = None,
    tags: list[str] | None = None,
    category: str | None = None,
    params: list[dict] | None = None,
    derived_from: dict | None = None,
) -> dict:
    import tempfile

    forge_code = forgecad_service.prepare_forge(forge_code)
    with tempfile.TemporaryDirectory(prefix="notion3d-forge-template-") as tmp:
        result = await forgecad_service.validate_forge_render(
            forge_code,
            Path(tmp),
        )

    meta = save_user_template(
        template_id=template_id,
        title=title,
        forge_code=forge_code,
        description=description,
        tags=tags,
        category=category,
        params=params,
        derived_from=derived_from,
    )
    if result.warnings:
        meta_path = settings.user_templates_dir / template_id / "meta.json"
        stored = json.loads(meta_path.read_text(encoding="utf-8"))
        stored["validation_warnings"] = result.warnings
        meta_path.write_text(
            json.dumps(stored, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        meta["validation_warnings"] = result.warnings
    return meta


def _infer_scad_params(scad_code: str) -> list[dict]:
    params: list[dict] = []
    stop_re = re.compile(
        r"^\s*(module|function|difference|union|intersection|minkowski|hull)\s*\("
    )
    for line in scad_code.split("\n"):
        if stop_re.match(line):
            break
        m = _ASSIGN_RE.match(line.strip())
        if m:
            params.append(
                {
                    "name": m.group(1),
                    "label": m.group(1),
                    "default": float(m.group(2)),
                    "unit": "mm",
                }
            )
    return params


def _infer_forge_params(forge_code: str) -> list[dict]:
    params: list[dict] = []
    seen: set[str] = set()
    for m in _FORGE_PARAM_RE.finditer(forge_code):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        params.append(
            {
                "name": name,
                "label": name,
                "default": float(m.group(2)),
                "unit": "mm",
            }
        )
    return params
