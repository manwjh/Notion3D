"""Read-only template library — ForgeCAD builtin + user dir."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import settings
from app.services import forgecad_service

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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
    return [
        ("builtin", settings.templates_dir / "builtin"),
        ("user", settings.user_templates_dir),
    ]


def _load_meta(entry_dir: Path) -> dict:
    meta_path = entry_dir / "meta.json"
    if not meta_path.exists():
        raise TemplateError(f"缺少 meta.json: {entry_dir.name}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.setdefault("id", entry_dir.name)
    if not (entry_dir / "model.forge.js").exists():
        raise TemplateError(f"模板缺少 model.forge.js: {entry_dir.name}")
    meta["format"] = "forge"
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
                    "format": "forge",
                    "params": meta.get("params") or [],
                }
            )
    return items


def get_template(template_id: str) -> dict:
    scope, entry_dir, meta = _resolve_entry(template_id)
    forge_path = entry_dir / "model.forge.js"
    if not forge_path.exists():
        raise TemplateError(f"模板缺少 model.forge.js: {template_id}")
    forge_code = forge_path.read_text(encoding="utf-8")
    forgecad_service.prepare_forge(forge_code)
    return {
        "id": meta["id"],
        "title": meta.get("title", meta["id"]),
        "description": meta.get("description"),
        "tags": meta.get("tags") or [],
        "category": meta.get("category"),
        "license": meta.get("license"),
        "source": meta.get("source", scope),
        "scope": scope,
        "format": "forge",
        "params": meta.get("params") or [],
        "forge_code": forge_code,
    }


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


def prepare_forge(template_id: str, params: dict[str, float] | None = None) -> tuple[dict, str]:
    detail = get_template(template_id)
    code = detail["forge_code"] or ""
    if params:
        code = apply_param_overrides_forge(code, params)
    code = forgecad_service.prepare_forge(code)
    return detail, code


def save_user_template(
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
    if not _SLUG_RE.match(template_id):
        raise TemplateError("模板 id 须为小写字母、数字与连字符")
    if (settings.user_templates_dir / template_id).exists():
        raise TemplateError(f"模板 id 已存在: {template_id}")

    entry_dir = settings.user_templates_dir / template_id
    entry_dir.mkdir(parents=True, exist_ok=False)

    forge_code = forgecad_service.prepare_forge(forge_code)
    (entry_dir / "model.forge.js").write_text(forge_code, encoding="utf-8")
    if params is None:
        params = _infer_forge_params(forge_code)

    meta = {
        "id": template_id,
        "title": title,
        "description": description,
        "tags": tags or [],
        "category": category,
        "license": "user",
        "source": "user",
        "format": "forge",
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
