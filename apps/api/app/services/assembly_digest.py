"""Spatial + modeling capability digest for Agent review."""

from __future__ import annotations

import json
from typing import Any

from app.services import storage
from app.services.forge_modeling import CAPABILITY_GAP_PREFIX


def build_spatial_digest(project_id: str, version: int) -> dict[str, Any] | None:
    parts_path = storage.version_dir(project_id, version) / "parts.json"
    if not parts_path.exists():
        return None

    try:
        data = json.loads(parts_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    assembly = data.get("assembly") or {}
    bboxes = list(assembly.get("bboxes") or [])
    spec = list(assembly.get("spec") or [])
    warnings = list(assembly.get("warnings") or [])
    capability = assembly.get("capability") or {}

    if not bboxes and not spec and not warnings and not capability:
        return None

    lines: list[str] = []
    if capability:
        strengths = capability.get("strengths") or []
        if strengths:
            lines.append(f"建模特征：{', '.join(strengths)}")
        next_steps = capability.get("next_steps") or []
        for step in next_steps:
            lines.append(f"→ {step}")

    if bboxes:
        lines.append(f"部件数 {len(bboxes)}，各件包围盒（mm）：")
        for entry in bboxes:
            center = entry.get("center") or [0, 0, 0]
            size = entry.get("size") or [0, 0, 0]
            label = entry.get("label") or entry.get("id") or "Part"
            lines.append(
                f"- {label}: center=({center[0]:.1f}, {center[1]:.1f}, {center[2]:.1f}), "
                f"size=({size[0]:.1f}, {size[1]:.1f}, {size[2]:.1f})"
            )

    if spec:
        lines.append("plan assembly_spec：")
        for module in spec:
            bits = [f"{module.get('id')} role={module.get('role', 'other')}"]
            if module.get("contains"):
                bits.append(f"contains={module['contains']}")
            if module.get("anchor"):
                bits.append(f"anchor={module['anchor']}")
            if module.get("hinge"):
                bits.append(f"hinge={module['hinge']}")
            lines.append(f"- {' · '.join(bits)}")

    recipes = _load_geometry_recipes(project_id, version)
    if recipes:
        lines.append("plan geometry_recipes：")
        for entry in recipes:
            lines.append(
                f"- {entry.get('part_id')}: recipe={entry.get('recipe')}"
                + (f" ({entry.get('notes')})" if entry.get("notes") else "")
            )

    if warnings:
        assembly_lines = [w for w in warnings if str(w).startswith("装配校验：")]
        capability_lines = [w for w in warnings if str(w).startswith(CAPABILITY_GAP_PREFIX)]
        if assembly_lines:
            lines.append("装配校验：")
            for warning in assembly_lines:
                lines.append(f"- {warning}")
        if capability_lines:
            lines.append("建模建议：")
            for warning in capability_lines:
                lines.append(f"- {warning}")

    review_checklist = _review_checklist(bboxes, spec, warnings, capability)

    return {
        "part_count": len(bboxes),
        "warnings": warnings,
        "summary": "\n".join(lines),
        "bboxes": bboxes,
        "assembly_spec": spec,
        "geometry_recipes": recipes,
        "capability": capability,
        "review_checklist": review_checklist,
    }


def _load_geometry_recipes(project_id: str, version: int) -> list[dict]:
    path = storage.version_dir(project_id, version) / "geometry_recipes.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data) if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _review_checklist(
    bboxes: list[dict],
    spec: list[dict],
    warnings: list[str],
    capability: dict,
) -> list[str]:
    items: list[str] = []
    if len(bboxes) >= 3:
        items.append("对照 spatial_digest 检查各部件 center 是否在同一装配簇内")
    if spec:
        items.append("逐项核对 assembly_spec 的 contains / anchor / hinge")
    if capability.get("advanced_modeling"):
        items.append("已使用特征级建模；核对比例、壁厚与 recipe 是否一致")
    elif capability.get("recipe_count", 0) > 0:
        items.append("按 geometry_recipes 补齐草图/放样/布尔特征（见 docs/forge-modeling-guide.md）")
    if warnings:
        items.append("存在装配或建模建议，可对照 spatial_digest 决定是否继续改 forge")
    if any(str(w).startswith(CAPABILITY_GAP_PREFIX) for w in warnings):
        items.append("可选：按 geometry_recipes 增强特征级建模")
    elif len(bboxes) >= 5:
        items.append("多部件装配：确认 Shell 空心、内部件在壳内、活动件相对位置合理")
    return items
