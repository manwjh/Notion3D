"""Design intent (fidelity) inference for plans and Engine snapshots."""

from __future__ import annotations

import re
from typing import Any

REALISM_KEYWORDS = re.compile(
    r"逼真|写实|照片|细节|精细|质感|雕刻|photo\s*real|realistic|high\s*fidelity",
    re.IGNORECASE,
)

DECORATIVE_KEYWORDS = re.compile(
    r"装饰|logo|地标|轮廓|卡通|人像|雕塑|figurine|character",
    re.IGNORECASE,
)


def infer_fidelity_fields(plan: dict[str, Any], user_text: str = "") -> dict[str, Any]:
    """Fill fidelity / high_fidelity_requested when Agent omitted them."""
    merged = dict(plan)
    blob = " ".join(
        [
            user_text or "",
            str(merged.get("summary") or ""),
            " ".join(str(a) for a in merged.get("assumptions") or []),
        ]
    )
    realism = bool(REALISM_KEYWORDS.search(blob))
    decorative = bool(DECORATIVE_KEYWORDS.search(blob))
    task_class = str(merged.get("task_class") or "A")

    if not merged.get("fidelity"):
        if task_class == "C" or decorative:
            merged["fidelity"] = "decorative"
        elif realism or task_class == "B":
            merged["fidelity"] = "layout_only"
        else:
            merged["fidelity"] = "printable"

    if "high_fidelity_requested" not in merged:
        merged["high_fidelity_requested"] = realism

    return merged


def design_intent_snapshot(plan: dict[str, Any]) -> dict[str, Any]:
    fidelity = plan.get("fidelity") or "printable"
    return {
        "fidelity": fidelity,
        "high_fidelity_requested": bool(plan.get("high_fidelity_requested")),
        "task_class": plan.get("task_class"),
    }
