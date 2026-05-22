"""Read-only template library — builtin repo + user data dir."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import settings
from app.services import cad_service

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ASSIGN_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([\d.]+)\s*;\s*(?://.*)?$")


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
            scad_path = entry_dir / "model.scad"
            if not scad_path.exists():
                continue
            meta = _load_meta(entry_dir)
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
                    "params": meta.get("params") or [],
                }
            )
    return items


def get_template(template_id: str) -> dict:
    scope, entry_dir, meta = _resolve_entry(template_id)
    scad_path = entry_dir / "model.scad"
    if not scad_path.exists():
        raise TemplateError(f"模板缺少 model.scad: {template_id}")
    scad_code = scad_path.read_text(encoding="utf-8")
    cad_service._sanitize_scad(scad_code)
    return {
        "id": meta["id"],
        "title": meta.get("title", meta["id"]),
        "description": meta.get("description"),
        "tags": meta.get("tags") or [],
        "category": meta.get("category"),
        "license": meta.get("license"),
        "source": meta.get("source", scope),
        "scope": scope,
        "params": meta.get("params") or [],
        "scad_code": scad_code,
    }


def apply_param_overrides(scad_code: str, params: dict[str, float]) -> str:
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


def prepare_scad(template_id: str, params: dict[str, float] | None = None) -> tuple[dict, str]:
    detail = get_template(template_id)
    scad = detail["scad_code"]
    if params:
        scad = apply_param_overrides(scad, params)
    scad = cad_service._sanitize_scad(scad)
    return detail, scad


def save_user_template(
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
    if not _SLUG_RE.match(template_id):
        raise TemplateError("模板 id 须为小写字母、数字与连字符")
    if (settings.user_templates_dir / template_id).exists():
        raise TemplateError(f"模板 id 已存在: {template_id}")

    scad_code = cad_service._sanitize_scad(scad_code)
    entry_dir = settings.user_templates_dir / template_id
    entry_dir.mkdir(parents=True, exist_ok=False)
    (entry_dir / "model.scad").write_text(scad_code, encoding="utf-8")

    if params is None:
        params = _infer_params(scad_code)

    meta = {
        "id": template_id,
        "title": title,
        "description": description,
        "tags": tags or [],
        "category": category,
        "license": "user",
        "source": "user",
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


def _infer_params(scad_code: str) -> list[dict]:
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
