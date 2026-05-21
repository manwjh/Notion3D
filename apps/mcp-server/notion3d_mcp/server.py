"""Notion3D MCP Server — tools for Cursor Agent, Claude Code, OpenClaw."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notion3d_mcp.client import Notion3DClient, format_json
from notion3d_mcp.enrich import enrich
from notion3d_mcp.links import resolve_web_base_from_health

mcp = FastMCP(
    "notion3d",
    instructions=(
        "Notion3D OpenSCAD engine (no LLM). YOU (the Agent) generate OpenSCAD — "
        "prefer notion3d_render_scad to submit SCAD for rendering. "
        "notion3d_template runs server-side rule templates only (cube/sphere/box), no LLM. "
        "Jobs are async: returns job_id — poll with notion3d_get_job or notion3d_wait_job. "
        "After success, share web_url with the user so they can preview/export in the browser. "
        "Follow the notion3d-openscad Skill for SCAD quality rules."
    ),
)

client = Notion3DClient()
_web_base_ready = False


def _ensure_web_base() -> None:
    global _web_base_ready
    if _web_base_ready:
        return
    try:
        resolve_web_base_from_health(client.health())
    except Exception:
        pass
    _web_base_ready = True


def _out(data: object) -> str:
    _ensure_web_base()
    return format_json(enrich(data))


@mcp.tool()
def notion3d_health() -> str:
    """Check Notion3D API and OpenSCAD availability."""
    health = client.health()
    resolve_web_base_from_health(health)
    global _web_base_ready
    _web_base_ready = True
    return format_json(health)


@mcp.tool()
def notion3d_list_projects() -> str:
    """List all Notion3D projects (same list as Web workbench)."""
    return _out(client.list_projects())


@mcp.tool()
def notion3d_create_project(name: str = "Agent 项目") -> str:
    """Create a project. Returns id, web_url — share web_url so user opens the workbench."""
    return _out(client.create_project(name=name))


@mcp.tool()
def notion3d_template(
    project_id: str,
    prompt: str,
    region: str | None = None,
    pick_x: float | None = None,
    pick_y: float | None = None,
    pick_z: float | None = None,
    pick_label: str | None = None,
) -> str:
    """Simple NL → rule-based OpenSCAD template (no LLM). Returns a render job.

    For complex models, generate OpenSCAD yourself and use notion3d_render_scad instead.
    """
    pick = None
    if pick_x is not None and pick_y is not None and pick_z is not None:
        pick = {
            "x": pick_x,
            "y": pick_y,
            "z": pick_z,
            "nx": 0.0,
            "ny": 1.0,
            "nz": 0.0,
            "label": pick_label,
        }
    job = client.template(project_id, prompt, pick=pick, region=region)
    return _out(
        {
            **job,
            "hint": "Poll notion3d_get_job or use notion3d_wait_job until status is succeeded/failed.",
        }
    )


@mcp.tool()
def notion3d_get_job(project_id: str, job_id: str) -> str:
    """Get job status (pending/running/succeeded/failed) with preview/STL phase info."""
    return _out(client.get_job(project_id, job_id))


@mcp.tool()
def notion3d_wait_job(project_id: str, job_id: str, max_wait_seconds: float = 600) -> str:
    """Poll a job until it succeeds or fails. Use for long STL renders."""
    return _out(client.wait_job(project_id, job_id, max_wait=max_wait_seconds))


@mcp.tool()
def notion3d_list_active_jobs(project_id: str) -> str:
    """List running/pending jobs for a project (for resume after disconnect)."""
    return _out(client.list_active_jobs(project_id))


@mcp.tool()
def notion3d_list_versions(project_id: str) -> str:
    """List model versions including preview_ready (partial) and complete."""
    return _out(client.list_versions(project_id))


@mcp.tool()
def notion3d_render_scad(
    project_id: str,
    scad_code: str,
    label: str = "MCP 渲染 SCAD",
) -> str:
    """Submit Agent-generated OpenSCAD source for rendering. Preferred path for complex models."""
    return _out(client.render_scad(project_id, scad_code, label=label))


@mcp.tool()
def notion3d_resume_stl(project_id: str, version: int) -> str:
    """Resume STL computation for a version that has preview but no STL yet."""
    return _out(client.resume_stl(project_id, version))


@mcp.tool()
def notion3d_list_messages(project_id: str) -> str:
    """List chat history for a project."""
    return _out(client.list_messages(project_id))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
