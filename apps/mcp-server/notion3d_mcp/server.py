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
        "always use notion3d_render_scad for modeling (submits SCAD, binds to active design turn). "
        "Do NOT use notion3d_template except for trivial test primitives in dev. "
        "Jobs are async: poll with notion3d_get_job or notion3d_wait_job. "
        "User is already in the Web workbench — do not ask them to open web_url. "
        "Follow notion3d-openscad Skill: parametric mm SCAD, validate before submit. "
        "For common shapes, check notion3d_list_templates before writing SCAD from scratch. "
        "Engine rejects non-manifold meshes."
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
    """Legacy rule-based NL→SCAD (no LLM). Dev/test only — prefer notion3d_render_scad."""
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
def notion3d_list_templates(
    tag: str | None = None,
    category: str | None = None,
    scope: str = "all",
) -> str:
    """Browse SCAD template library (builtin + user-saved). Filter by tag or category."""
    return _out(client.list_templates(tag=tag, category=category, scope=scope))


@mcp.tool()
def notion3d_get_template(template_id: str) -> str:
    """Get template metadata and full SCAD source by id."""
    return _out(client.get_template(template_id))


@mcp.tool()
def notion3d_apply_template(
    template_id: str,
    project_id: str | None = None,
    name: str | None = None,
    label: str | None = None,
    params_json: str | None = None,
) -> str:
    """Apply a library template to a project (creates project if project_id omitted).

    params_json: optional JSON object of param overrides, e.g. {"size": 40, "module_mm": 2}.
    For heavy edits: notion3d_get_template → modify SCAD → notion3d_render_scad.
    """
    import json

    params = json.loads(params_json) if params_json else None
    result = client.apply_template(
        template_id,
        project_id=project_id,
        name=name,
        label=label,
        params=params,
    )
    return _out(
        {
            **result,
            "hint": "Poll notion3d_get_job or use notion3d_wait_job until status is succeeded/failed.",
        }
    )


@mcp.tool()
def notion3d_save_template(
    project_id: str,
    version: int,
    template_id: str,
    title: str,
    description: str | None = None,
    tags: str | None = None,
    category: str | None = None,
) -> str:
    """Save a project version as a user template for reuse (comma-separated tags)."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    return _out(
        client.save_template(
            project_id,
            version,
            template_id=template_id,
            title=title,
            description=description,
            tags=tag_list,
            category=category,
        )
    )


@mcp.tool()
def notion3d_render_scad(
    project_id: str,
    scad_code: str,
    label: str = "MCP 渲染 SCAD",
) -> str:
    """Submit Agent-generated OpenSCAD for STL rendering.

    Preferred for complex models. Engine rejects SCAD that produces non-closed meshes.
    See notion3d-openscad skill for domain examples and validation.
    """
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
