"""ForgeCAD positive design capability — recipes, plan enrichment, capability digest."""

from __future__ import annotations

import re
from typing import Any

CAPABILITY_GAP_PREFIX = "建模建议："

# Recipe ids align with plan.geometry_recipes[].recipe and forge-capability.mjs
RECIPE_CATALOG: dict[str, dict[str, str]] = {
    "sketch_extrude": {
        "label": "草图拉伸实体",
        "summary": "constrainedSketch 轮廓 → .extrude(厚度) → 可选 fillet",
        "for_roles": "支架、凸台、安装板、简单外壳壁",
    },
    "sketch_extrude_shell": {
        "label": "草图拉伸空心壳",
        "summary": "外轮廓 extrude → subtract 内腔 → fillet 外棱；外壳/盒体首选",
        "for_roles": "shell、enclosure、盒体",
    },
    "loft": {
        "label": "截面放样",
        "summary": "spline2d/polygon 多截面 → loft(stations) → refine/smoothOut",
        "for_roles": "流线外形、盖面、船型、圆润机身",
    },
    "sweep": {
        "label": "扫掠",
        "summary": "profile + path → sweep()",
        "for_roles": "管路、把手、密封条路径",
    },
    "revolve": {
        "label": "旋转体",
        "summary": "轮廓 revolve 或 cylinder 台阶 + subtract",
        "for_roles": "旋钮、杯状件、回转对称件",
    },
    "union_bracket": {
        "label": "板件并集支架",
        "summary": "union(box...) + fillet/chamfer；L/T 支架",
        "for_roles": "支架、角码、加强筋板",
    },
    "primitive_shell": {
        "label": "回转壳体（简易）",
        "summary": "cylinder 外壁 subtract 内腔；仅用于回转对称且时间紧的壳",
        "for_roles": "圆筒外壳（无复杂拔模）",
    },
    "primitive_layout": {
        "label": "布局级体素",
        "summary": "box/cylinder 布尔组合；仅 layout_only 内部件或占位",
        "for_roles": "internal、B 类内部布局",
    },
}

_ROLE_DEFAULT_RECIPE: dict[str, str] = {
    "shell": "sketch_extrude_shell",
    "lid": "sketch_extrude",
    "internal": "primitive_layout",
    "external": "sketch_extrude",
    "other": "sketch_extrude",
}

_TASK_CLASS_DEFAULT_RECIPE: dict[str, str] = {
    "A": "sketch_extrude",
    "B": "sketch_extrude_shell",
    "C": "primitive_layout",
}

_FEATURE_PATTERNS: dict[str, re.Pattern[str]] = {
    "constrainedSketch": re.compile(r"\bconstrainedSketch\s*\("),
    "extrude": re.compile(r"\.extrude\s*\(|\bextrude\s*\("),
    "loft": re.compile(r"\bloft\s*\("),
    "sweep": re.compile(r"\bsweep\s*\("),
    "fillet": re.compile(r"\.fillet\s*\(|\bfillet\s*\("),
    "chamfer": re.compile(r"\.chamfer\s*\(|\bchamfer\s*\("),
    "revolve": re.compile(r"\brevolve\s*\("),
    "subtract": re.compile(r"\.subtract\s*\("),
    "union": re.compile(r"\bunion\s*\("),
    "spline2d": re.compile(r"\bspline2d\s*\("),
    "sphere": re.compile(r"\bsphere\s*\("),
    "box": re.compile(r"\bbox\s*\("),
    "cylinder": re.compile(r"\bcylinder\s*\("),
}

_RECIPE_REQUIRED_FEATURES: dict[str, list[str]] = {
    "sketch_extrude": ["constrainedSketch", "extrude"],
    "sketch_extrude_shell": ["constrainedSketch", "extrude", "subtract"],
    "loft": ["loft"],
    "sweep": ["sweep"],
    "revolve": ["revolve"],
    "union_bracket": ["union"],
    "primitive_shell": ["cylinder", "subtract"],
    "primitive_layout": [],
}

_BUILTIN_TEMPLATE_RECIPES: dict[str, str] = {
    "hello-assembly": "primitive_shell",
    "open-enclosure": "sketch_extrude_shell",
    "sketch-bracket": "union_bracket",
    "sketch-enclosure": "sketch_extrude_shell",
    "loft-hull": "loft",
}


def default_recipe_for_role(role: str, task_class: str = "A") -> str:
    if task_class == "C":
        return "primitive_layout"
    return _ROLE_DEFAULT_RECIPE.get(role or "other", _TASK_CLASS_DEFAULT_RECIPE.get(task_class, "sketch_extrude"))


def enrich_plan_geometry_recipes(plan: dict[str, Any]) -> dict[str, Any]:
    """Ensure every assembly module has a geometry recipe (plan-time positive contract)."""
    merged = dict(plan)
    existing = list(merged.get("geometry_recipes") or [])
    if existing:
        return merged

    assembly_spec = list(merged.get("assembly_spec") or [])
    task_class = str(merged.get("task_class") or "A")
    recipes: list[dict[str, Any]] = []

    for module in assembly_spec:
        part_id = str(module.get("id") or "").strip()
        if not part_id:
            continue
        role = str(module.get("role") or "other")
        recipe = default_recipe_for_role(role, task_class)
        recipes.append(
            {
                "part_id": part_id,
                "recipe": recipe,
                "notes": RECIPE_CATALOG.get(recipe, {}).get("summary", ""),
            }
        )

    if not recipes:
        modules = list(merged.get("modules") or [])
        for part_id in modules:
            if part_id:
                recipes.append(
                    {
                        "part_id": str(part_id),
                        "recipe": _TASK_CLASS_DEFAULT_RECIPE.get(task_class, "sketch_extrude"),
                        "notes": "",
                    }
                )

    if not recipes and task_class != "C":
        recipes.append(
            {
                "part_id": "MainPart",
                "recipe": _TASK_CLASS_DEFAULT_RECIPE.get(task_class, "sketch_extrude"),
                "notes": "单件或未列 assembly_spec 时的默认特征策略",
            }
        )

    if recipes:
        merged["geometry_recipes"] = recipes
    return merged


def detect_forge_features(forge_source: str) -> dict[str, int]:
    text = forge_source or ""
    return {name: len(pat.findall(text)) for name, pat in _FEATURE_PATTERNS.items()}


def analyze_forge_capability(
    forge_source: str,
    geometry_recipes: list[dict[str, Any]] | None = None,
    *,
    design_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Positive capability report + gap warnings for spatial_digest / validation."""
    features = detect_forge_features(forge_source)
    recipes = list(geometry_recipes or [])
    design_intent = design_intent or {}
    task_class = str(design_intent.get("task_class") or "A")
    fidelity = str(design_intent.get("fidelity") or "printable")

    used_ops = [name for name, count in features.items() if count > 0]
    advanced = any(
        features.get(k, 0) > 0
        for k in ("constrainedSketch", "loft", "sweep", "revolve", "fillet", "chamfer")
    )

    strengths: list[str] = []
    if features.get("constrainedSketch", 0) > 0:
        strengths.append("约束草图")
    if features.get("extrude", 0) > 0:
        strengths.append("拉伸")
    if features.get("loft", 0) > 0:
        strengths.append("放样")
    if features.get("fillet", 0) > 0:
        strengths.append("圆角")
    if features.get("subtract", 0) > 0:
        strengths.append("布尔减腔")

    gaps: list[str] = []
    for entry in recipes:
        part_id = str(entry.get("part_id") or "")
        recipe = str(entry.get("recipe") or "")
        required = _RECIPE_REQUIRED_FEATURES.get(recipe, [])
        missing = [f for f in required if features.get(f, 0) <= 0]
        if missing and part_id:
            label = RECIPE_CATALOG.get(recipe, {}).get("label", recipe)
            gaps.append(
                f"{CAPABILITY_GAP_PREFIX}部件 {part_id} 计划为「{label}」，"
                f"脚本未检测到 {', '.join(missing)}；可考虑 {RECIPE_CATALOG.get(recipe, {}).get('summary', recipe)}"
            )

    next_steps: list[str] = []
    if gaps:
        next_steps.append("可选：按 geometry_recipes 为各部件补齐 ForgeCAD 特征（见 docs/forge-modeling-guide.md）")
    elif not advanced and recipes:
        next_steps.append("已满足 recipe 最低特征；可加 fillet 或拆分 src/ 子模块提升细节")
    elif advanced:
        next_steps.append("特征级建模已启用；对照 spatial_digest 检查比例与装配")

    return {
        "features": features,
        "used_operations": used_ops,
        "strengths": strengths,
        "advanced_modeling": advanced,
        "gaps": gaps,
        "next_steps": next_steps,
        "recipe_count": len(recipes),
    }


def modeling_guide_excerpt_for_prompt() -> str:
    """Compact positive-design section injected into Web Turn agent prompt."""
    lines = [
        "## 正向建模（ForgeCAD）",
        "",
        "真源：docs/forge-modeling-guide.md。",
        "render-first：优先 render_forge，再按 spatial_digest / warnings 迭代。",
        "geometry_recipes 与 report_design_plan 为**可选归档**，非 render 门禁。",
        "",
        "| recipe | 典型做法 |",
        "|--------|------|",
    ]
    for rid, meta in RECIPE_CATALOG.items():
        lines.append(f"| `{rid}` | {meta['summary']} |")
    lines.extend(
        [
            "",
            "内置模板（可选起点）：sketch-bracket · sketch-enclosure · loft-hull · hello-assembly",
            "",
            "复杂件：src/part-name.forge.js + importAssembly；外壳 name 含 Shell → Web 半透明。",
            "全量 API：cd apps/forge-runner && npx forgecad skill install",
        ]
    )
    return "\n".join(lines)


def recipe_for_template(template_id: str) -> str | None:
    return _BUILTIN_TEMPLATE_RECIPES.get(template_id)
