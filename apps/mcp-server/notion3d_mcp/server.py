"""Notion3D MCP Server — Agent hosts integrate via notion3d_* tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notion3d_mcp.client import Notion3DClient, format_json
from notion3d_mcp.enrich import enrich
from notion3d_mcp.links import resolve_web_base_from_health

mcp = FastMCP(
    "notion3d",
    instructions=(
        "Notion3D ForgeCAD engine (no LLM). Start from notion3d-pipeline Skill, then: "
        "notion3d-intake → notion3d-plan → notion3d-forge-author → notion3d-mcp → notion3d-review. "
        "Before authoring: notion3d_report_design_plan. "
        "Model with notion3d_render_forge + notion3d_wait_job. "
        "After render: notion3d_report_design_review. "
        "User is in Web workbench — do not ask for web_url."
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
    """Check Notion3D API and ForgeCAD availability."""
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
    """List model versions (pending or complete)."""
    return _out(client.list_versions(project_id))


@mcp.tool()
def notion3d_get_forge_sources(project_id: str, version: int) -> str:
    """Read model.forge.js and src/ sub-files for a version.

    Use before editing multi-file assemblies (importAssembly). Returns forge_code
    and files dict suitable for notion3d_render_forge files_json.
    """
    return _out(client.get_forge_sources(project_id, version))


@mcp.tool()
def notion3d_list_templates(
    tag: str | None = None,
    category: str | None = None,
    scope: str = "all",
) -> str:
    """Browse template library. Demo use only — default modeling is from_scratch."""
    return _out(client.list_templates(tag=tag, category=category, scope=scope))


@mcp.tool()
def notion3d_get_template(template_id: str) -> str:
    """Get template metadata and forge_code by id."""
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
    For heavy edits: notion3d_get_template → modify forge_code → notion3d_render_forge.
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
def notion3d_render_forge(
    project_id: str,
    forge_code: str,
    label: str = "MCP 渲染 ForgeCAD",
    files_json: str | None = None,
) -> str:
    """Submit Agent-generated ForgeCAD (.forge.js) for assembly render.

    Preferred path for multi-part models. Returns parts.json for Web assembly viewer.
    Optional files_json: JSON object of sub-files under src/, e.g.
    {"motor.forge.js": "return box(10,10,10);"} for importAssembly("src/motor.forge.js").
    See notion3d-forge-author skill.
    """
    files = None
    if files_json:
        import json

        files = json.loads(files_json)
        if not isinstance(files, dict):
            raise ValueError("files_json must be a JSON object")
    return _out(client.render_forge(project_id, forge_code, label=label, files=files))


@mcp.tool()
def notion3d_list_messages(project_id: str) -> str:
    """List chat history for a project."""
    return _out(client.list_messages(project_id))


@mcp.tool()
def notion3d_get_design_state(project_id: str) -> str:
    """Get active design turn phase, plan, and review artifacts."""
    return _out(client.get_design_state(project_id))


@mcp.tool()
def notion3d_report_design_plan(
    project_id: str,
    task_class: str,
    summary: str,
    strategy: str,
    turn_id: str | None = None,
    template_id: str | None = None,
    params_json: str | None = None,
    modules_json: str | None = None,
    assumptions_json: str | None = None,
) -> str:
    """Record modeling plan before authoring ForgeCAD. Advances turn to author (or blocked for class C).

    task_class: A | B | C
    strategy: template_apply | template_edit | from_scratch | chat_only
    """
    import json

    params = json.loads(params_json) if params_json else None
    modules = json.loads(modules_json) if modules_json else None
    assumptions = json.loads(assumptions_json) if assumptions_json else None
    return _out(
        client.report_design_plan(
            project_id,
            task_class=task_class,
            summary=summary,
            strategy=strategy,
            turn_id=turn_id,
            template_id=template_id,
            params=params,
            modules=modules,
            assumptions=assumptions,
        )
    )


@mcp.tool()
def notion3d_report_design_review(
    project_id: str,
    status: str,
    turn_id: str | None = None,
    notes_json: str | None = None,
    retry_phase: str | None = None,
) -> str:
    """Record design review after render. status: pass | retry | accept_warnings. retry_phase: plan | author."""
    import json

    notes = json.loads(notes_json) if notes_json else None
    return _out(
        client.report_design_review(
            project_id,
            status=status,
            turn_id=turn_id,
            notes=notes,
            retry_phase=retry_phase,
        )
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
