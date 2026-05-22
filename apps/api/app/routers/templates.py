"""Template library — list, read, apply, save."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.models.schemas import (
    JobSource,
    ProjectOut,
    SaveTemplateIn,
    TemplateApplyIn,
    TemplateApplyOut,
    TemplateDetailOut,
    TemplateOut,
    TemplateParamOut,
)
from app.services import job_service, storage, template_library
from app.services.job_present import job_to_out

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _template_out(item: dict) -> TemplateOut:
    return TemplateOut(
        id=item["id"],
        title=item["title"],
        description=item.get("description"),
        tags=item.get("tags") or [],
        category=item.get("category"),
        license=item.get("license"),
        source=item.get("source"),
        scope=item["scope"],
        params=[TemplateParamOut(**p) for p in item.get("params") or []],
    )


def _template_detail(item: dict) -> TemplateDetailOut:
    base = _template_out(item)
    return TemplateDetailOut(**base.model_dump(), scad_code=item["scad_code"])


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    tag: str | None = Query(default=None),
    category: str | None = Query(default=None),
    scope: str = Query(default="all", pattern="^(all|builtin|user)$"),
) -> list[TemplateOut]:
    items = template_library.list_templates(tag=tag, category=category, scope=scope)
    return [_template_out(item) for item in items]


@router.get("/{template_id}", response_model=TemplateDetailOut)
async def get_template(template_id: str) -> TemplateDetailOut:
    try:
        item = template_library.get_template(template_id)
    except template_library.TemplateError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _template_detail(item)


@router.post("/{template_id}/apply", response_model=TemplateApplyOut)
async def apply_template(
    template_id: str,
    body: TemplateApplyIn,
    background_tasks: BackgroundTasks,
) -> TemplateApplyOut:
    try:
        meta, scad_code = template_library.prepare_scad(template_id, body.params)
    except template_library.TemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    project: ProjectOut
    if body.project_id:
        existing = storage.get_project(body.project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="项目不存在")
        project = existing
    else:
        project_name = body.name or meta["title"]
        project = storage.create_project(project_name)

    label = body.label or f"模板: {meta['title']}"
    job = job_service.create_render_job(
        project.id,
        scad_code,
        label,
        source=JobSource.template.value,
    )
    background_tasks.add_task(job_service.run_render_scad_job, job["id"])

    return TemplateApplyOut(
        project=project,
        job=job_to_out(job),
        template_id=template_id,
    )
