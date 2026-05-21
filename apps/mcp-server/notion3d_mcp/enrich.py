"""Enrich MCP tool JSON with web workbench links."""

from __future__ import annotations

from typing import Any

from notion3d_mcp.links import project_url


def _project_id(data: dict[str, Any]) -> str | None:
    pid = data.get("project_id") or data.get("id")
    return str(pid) if pid else None


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

    if out.get("status") == "succeeded" and pid:
        out.setdefault(
            "next_step",
            f"建模完成。请告诉用户在浏览器打开：{project_url(pid)}",
        )

    return out
