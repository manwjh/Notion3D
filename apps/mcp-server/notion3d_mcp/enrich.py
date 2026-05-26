"""Enrich MCP tool JSON with web workbench links."""

from __future__ import annotations

from typing import Any

from notion3d_mcp.links import project_url

ASSEMBLY_WARNING_PREFIX = "装配校验："
CAPABILITY_GAP_PREFIX = "建模建议："


def _project_id(data: dict[str, Any]) -> str | None:
    pid = data.get("project_id") or data.get("id")
    return str(pid) if pid else None


def _enrich_job(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if out.get("status") != "succeeded":
        return out

    digest = out.get("spatial_digest")
    if isinstance(digest, dict) and digest.get("summary"):
        out.setdefault("spatial_summary", digest["summary"])

    warnings = list(out.get("validation_warnings") or [])
    assembly_warnings = [w for w in warnings if str(w).startswith(ASSEMBLY_WARNING_PREFIX)]
    capability_warnings = [w for w in warnings if str(w).startswith(CAPABILITY_GAP_PREFIX)]

    checklist: list[str] = []
    if isinstance(digest, dict):
        checklist = list(digest.get("review_checklist") or [])

    if assembly_warnings or capability_warnings or checklist:
        lines = ["渲染完成。校验提示为可选改进（不阻塞交付）："]
        if capability_warnings:
            lines.append("- 建模提示（可继续迭代 forge 代码）")
            lines.extend(f"  · {w}" for w in capability_warnings[:6])
        if assembly_warnings:
            lines.append("- 装配提示（可检查 translate / contains）")
            lines.extend(f"  · {w}" for w in assembly_warnings[:6])
        if isinstance(digest, dict):
            cap = digest.get("capability") or {}
            strengths = cap.get("strengths") or []
            if strengths:
                lines.append(f"- 已用特征：{', '.join(strengths)}")
            next_steps = cap.get("next_steps") or []
            for step in next_steps[:4]:
                lines.append(f"  → {step}")
        if checklist:
            lines.append("- 可选核对：")
            lines.extend(f"  · {item}" for item in checklist)
        if isinstance(digest, dict) and digest.get("summary"):
            lines.append("- spatial_summary / spatial_digest 已附")
        out["review_hint"] = "\n".join(lines)
        out.setdefault(
            "next_step",
            "对照 spatial_digest 与用户反馈；满意则回复用户，否则 get_forge_sources → 改稿 → render_forge。",
        )
    elif out.get("version") and isinstance(digest, dict):
        out.setdefault(
            "next_step",
            "渲染成功。对照 spatial_digest；用户满意则简短总结，否则继续迭代 forge。",
        )
    elif out.get("status") == "succeeded":
        out.setdefault(
            "next_step",
            "渲染完成。向用户说明结果；需要调整则 get_forge_sources → render_forge。",
        )

    return out


def enrich(data: Any) -> Any:
    if isinstance(data, list):
        return [enrich(item) for item in data]
    if not isinstance(data, dict):
        return data

    out = dict(data)
    pid = _project_id(out)
    if pid:
        url = project_url(pid)
        out.setdefault("web_url", url)
        out.setdefault(
            "view_in_browser",
            f"在浏览器打开 Notion3D 工作台：{url}",
        )

    if out.get("kind") == "render" or "validation_warnings" in out:
        out = _enrich_job(out)
    elif out.get("status") == "succeeded" and pid:
        out.setdefault(
            "next_step",
            f"建模完成。请告诉用户在浏览器打开：{project_url(pid)}",
        )

    return out
