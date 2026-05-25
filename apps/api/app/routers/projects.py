from datetime import datetime
import logging
import re

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, Response

from app.models.schemas import (
    ChatMessageOut,
    ForgePreviewOut,
    ForgeRenderIn,
    ForgeSourcesOut,
    JobOut,
    JobSource,
    ModelVersionOut,
    ProjectCreate,
    ProjectOut,
    SaveTemplateIn,
    ScadRenderIn,
    TemplateJobIn,
    TemplateOut,
    TemplateParamOut,
    VersionStatus,
)
from app.services.cad_backend import CadBackend
from app.services import (
    cad_service,
    chat_present,
    design_turn,
    forge_preview_service,
    forgecad_service,
    job_service,
    job_store,
    storage,
    template_library,
)
from app.services.job_present import job_to_out as _job_to_out

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _version_meta(out_dir) -> dict:
    meta_file = out_dir / "meta.json"
    if not meta_file.exists():
        return {}
    import json

    return json.loads(meta_file.read_text(encoding="utf-8"))


def _version_status(out_dir, meta: dict) -> VersionStatus:
    if meta.get("status") == "complete" or (out_dir / "model.stl").exists():
        return VersionStatus.complete
    if meta.get("status") == "preview_ready" or (out_dir / "preview.png").exists():
        return VersionStatus.preview_ready
    if (out_dir / "model.forge.js").exists() or (out_dir / "model.scad").exists():
        return VersionStatus.pending
    return VersionStatus.pending


def _version_created_at(out_dir) -> datetime:
    stl = out_dir / "model.stl"
    if stl.exists():
        return datetime.fromtimestamp(stl.stat().st_mtime)
    forge = out_dir / "model.forge.js"
    if forge.exists():
        return datetime.fromtimestamp(forge.stat().st_mtime)
    scad = out_dir / "model.scad"
    if scad.exists():
        return datetime.fromtimestamp(scad.stat().st_mtime)
    return datetime.fromtimestamp(out_dir.stat().st_mtime)


def _design_fields_from_version_meta(meta: dict) -> dict:
    plan = meta.get("design_plan") or {}
    review = meta.get("design_review") or {}
    return {
        "plan_summary": plan.get("summary"),
        "plan_strategy": plan.get("strategy"),
        "plan_template_id": plan.get("template_id"),
        "plan_assumptions": plan.get("assumptions") or [],
        "plan_modules": plan.get("modules") or [],
        "review_status": review.get("status"),
        "review_notes": review.get("notes") or [],
        "design_revision": meta.get("design_revision"),
    }


def _version_out(project_id: str, v: int, out_dir) -> ModelVersionOut:
    stl = out_dir / "model.stl"
    parts = out_dir / "parts.json"
    meta = _version_meta(out_dir)
    status = _version_status(out_dir, meta)
    forge = out_dir / "model.forge.js"
    scad = out_dir / "model.scad"
    src_files = forgecad_service.list_src_files(out_dir) if forge.exists() else []
    return ModelVersionOut(
        version=v,
        status=status,
        stl_url=(
            f"/api/projects/{project_id}/versions/{v}/model.stl"
            if stl.exists()
            else None
        ),
        parts_url=(
            f"/api/projects/{project_id}/versions/{v}/parts.json"
            if parts.exists()
            else None
        ),
        forge_url=(
            f"/api/projects/{project_id}/versions/{v}/model.forge.js"
            if forge.exists()
            else None
        ),
        scad_url=(
            f"/api/projects/{project_id}/versions/{v}/model.scad"
            if scad.exists()
            else None
        ),
        preview_url=(
            f"/api/projects/{project_id}/versions/{v}/preview.png"
            if (out_dir / "preview.png").exists()
            else None
        ),
        created_at=_version_created_at(out_dir),
        prompt=meta.get("prompt"),
        turn_id=meta.get("turn_id"),
        job_id=meta.get("job_id"),
        validation_warnings=meta.get("validation_warnings") or [],
        cad_backend=meta.get("cad_backend") or CadBackend.forgecad.value,
        src_files=src_files,
        forge_sources_url=(
            f"/api/projects/{project_id}/versions/{v}/forge-sources"
            if forge.exists()
            else None
        ),
        **_design_fields_from_version_meta(meta),
    )


@router.get("", response_model=list[ProjectOut])
async def list_projects() -> list[ProjectOut]:
    return storage.list_projects()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate) -> ProjectOut:
    return storage.create_project(body.name)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str) -> ProjectOut:
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str) -> None:
    if not storage.delete_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")


@router.get("/{project_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(project_id: str) -> list[ChatMessageOut]:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return chat_present.messages_out(project_id)


@router.post("/{project_id}/jobs/template", response_model=JobOut)
async def create_template_job(
    project_id: str,
    body: TemplateJobIn,
    background_tasks: BackgroundTasks,
) -> JobOut:
    """Rule-based NL → SCAD (no LLM). Used by MCP notion3d_template."""
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    pick = body.pick.model_dump() if body.pick else None
    job = job_service.create_template_job(
        project_id,
        body.prompt,
        pick=pick,
        region=body.region,
    )
    background_tasks.add_task(job_service.run_template_job, job["id"])
    return _job_to_out(job)


@router.post("/{project_id}/render-forge", response_model=JobOut)
async def render_forge(
    project_id: str,
    body: ForgeRenderIn,
    background_tasks: BackgroundTasks,
) -> JobOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    try:
        forge_code = forgecad_service.prepare_forge(body.forge_code)
    except cad_service.CadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source = body.source.value
    turn_id = design_turn.active_turn_id(project_id) if source == JobSource.agent.value else None

    job = job_service.create_render_job(
        project_id,
        forge_code,
        body.label,
        turn_id=turn_id,
        source=source,
        backend=CadBackend.forgecad,
        forge_files=body.files,
    )
    static_warnings = forgecad_service.static_forge_warnings(forge_code, body.files)
    if static_warnings:
        job_service.update_job(job["id"], validation_warnings=static_warnings)
        job = job_service.get_job(job["id"]) or job
    if turn_id:
        design_turn.register_job(project_id, turn_id, job["id"], prompt=body.label)
    background_tasks.add_task(job_service.run_render_forge_job, job["id"])
    return _job_to_out(job)


@router.post("/{project_id}/render-scad", response_model=JobOut)
async def render_scad(
    project_id: str,
    body: ScadRenderIn,
    background_tasks: BackgroundTasks,
) -> JobOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    try:
        scad_code = cad_service.prepare_scad(body.scad_code)
    except cad_service.CadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source = body.source.value
    turn_id = design_turn.active_turn_id(project_id) if source == JobSource.agent.value else None

    job = job_service.create_render_job(
        project_id,
        scad_code,
        body.label,
        turn_id=turn_id,
        source=source,
        backend=CadBackend.openscad_legacy,
    )
    static_warnings = cad_service.static_scad_warnings(scad_code)
    if static_warnings:
        job_service.update_job(job["id"], validation_warnings=static_warnings)
        job = job_service.get_job(job["id"]) or job
    if turn_id:
        design_turn.register_job(project_id, turn_id, job["id"], prompt=body.label)
    background_tasks.add_task(job_service.run_render_scad_job, job["id"])
    return _job_to_out(job)


@router.get("/{project_id}/jobs/active", response_model=list[JobOut])
async def list_active_jobs(project_id: str) -> list[JobOut]:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return [_job_to_out(job) for job in job_store.list_active_jobs(project_id)]


@router.get("/{project_id}/jobs/{job_id}", response_model=JobOut)
async def get_job(project_id: str, job_id: str) -> JobOut:
    job = job_service.get_job(job_id)
    if not job or job["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _job_to_out(job)


@router.get("/{project_id}/versions", response_model=list[ModelVersionOut])
async def list_versions(project_id: str) -> list[ModelVersionOut]:
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    versions: list[ModelVersionOut] = []
    if not project.latest_version:
        return versions

    for v in range(1, project.latest_version + 1):
        out_dir = storage.version_dir(project_id, v)
        forge = out_dir / "model.forge.js"
        scad = out_dir / "model.scad"
        preview = out_dir / "preview.png"
        stl = out_dir / "model.stl"
        if not forge.exists() and not scad.exists() and not preview.exists() and not stl.exists():
            continue
        versions.append(_version_out(project_id, v, out_dir))
    return versions


@router.post("/{project_id}/versions/{version}/resume-stl", response_model=JobOut)
async def resume_version_stl(
    project_id: str,
    version: int,
    background_tasks: BackgroundTasks,
) -> JobOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        job = await job_service.resume_version_stl(project_id, version)
    except cad_service.CadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    background_tasks.add_task(job_service.run_render_scad_job, job["id"])
    return _job_to_out(job)


@router.get("/{project_id}/versions/{version}/parts.json")
async def download_parts_manifest(project_id: str, version: int):
    path = storage.version_dir(project_id, version) / "parts.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="部件清单不存在")
    import json

    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/{project_id}/versions/{version}/parts/{part_id}.stl")
async def download_part_stl(project_id: str, version: int, part_id: str) -> FileResponse:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", part_id):
        raise HTTPException(status_code=400, detail="无效的部件 ID")
    path = storage.version_dir(project_id, version) / "parts" / f"{part_id}.stl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="部件 STL 不存在")
    return FileResponse(path, media_type="model/stl", filename=f"{part_id}_v{version}.stl")


@router.get("/{project_id}/versions/{version}/model.stl")
async def download_stl(project_id: str, version: int) -> FileResponse:
    path = storage.version_dir(project_id, version) / "model.stl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="STL 不存在")
    return FileResponse(path, media_type="model/stl", filename=f"model_v{version}.stl")


@router.post("/{project_id}/versions/{version}/forge-preview", response_model=ForgePreviewOut)
async def start_forge_preview(project_id: str, version: int) -> ForgePreviewOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    result = await forge_preview_service.ensure_preview(project_id, version)
    if not result.get("ready"):
        raise HTTPException(status_code=503, detail=result.get("error") or "预览不可用")
    return ForgePreviewOut(**result)


@router.get("/{project_id}/versions/{version}/forge-sources", response_model=ForgeSourcesOut)
async def get_forge_sources(project_id: str, version: int) -> ForgeSourcesOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    out_dir = storage.version_dir(project_id, version)
    try:
        sources = forgecad_service.read_forge_sources(out_dir)
    except cad_service.CadError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    meta = _version_meta(out_dir)
    return ForgeSourcesOut(
        version=version,
        forge_code=str(sources["forge_code"]),
        files=dict(sources["files"]),
        cad_backend=meta.get("cad_backend") or CadBackend.forgecad.value,
    )


@router.get("/{project_id}/versions/{version}/src/{file_path:path}")
async def download_forge_src(project_id: str, version: int, file_path: str) -> FileResponse:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    out_dir = storage.version_dir(project_id, version)
    try:
        content = forgecad_service.read_src_file(out_dir, file_path)
    except cad_service.CadError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rel = file_path.strip().lstrip("/").replace("\\", "/")
    filename = rel.replace("/", "_")
    return Response(
        content=content,
        media_type="text/javascript",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/{project_id}/versions/{version}/model.forge.js")
async def download_forge(project_id: str, version: int) -> FileResponse:
    path = storage.version_dir(project_id, version) / "model.forge.js"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Forge 源码不存在")
    return FileResponse(path, media_type="text/javascript", filename=f"model_v{version}.forge.js")


@router.get("/{project_id}/versions/{version}/model.scad")
async def download_scad(project_id: str, version: int) -> FileResponse:
    path = storage.version_dir(project_id, version) / "model.scad"
    if not path.exists():
        raise HTTPException(status_code=404, detail="SCAD 不存在")
    return FileResponse(path, media_type="text/plain", filename=f"model_v{version}.scad")


@router.get("/{project_id}/versions/{version}/preview.png")
async def download_preview(project_id: str, version: int) -> FileResponse:
    path = storage.version_dir(project_id, version) / "preview.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="预览图不存在")
    return FileResponse(path, media_type="image/png")


@router.post("/{project_id}/versions/{version}/save-template", response_model=TemplateOut)
async def save_version_as_template(
    project_id: str,
    version: int,
    body: SaveTemplateIn,
) -> TemplateOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    scad_path = storage.version_dir(project_id, version) / "model.scad"
    forge_path = storage.version_dir(project_id, version) / "model.forge.js"
    if not scad_path.exists() and not forge_path.exists():
        raise HTTPException(status_code=404, detail="该版本尚无建模源码")

    if forge_path.exists():
        forge_code = forge_path.read_text(encoding="utf-8")
        try:
            meta = await template_library.save_user_forge_template_validated(
                template_id=body.id,
                title=body.title,
                forge_code=forge_code,
                description=body.description,
                tags=body.tags,
                category=body.category,
                derived_from={
                    "project_id": project_id,
                    "version": version,
                },
            )
        except template_library.TemplateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except cad_service.CadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        scad_code = scad_path.read_text(encoding="utf-8")
        try:
            meta = await template_library.save_user_template_validated(
                template_id=body.id,
                title=body.title,
                scad_code=scad_code,
                description=body.description,
                tags=body.tags,
                category=body.category,
                derived_from={
                    "project_id": project_id,
                    "version": version,
                },
            )
        except template_library.TemplateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except cad_service.CadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TemplateOut(
        id=meta["id"],
        title=meta["title"],
        description=meta.get("description"),
        tags=meta.get("tags") or [],
        category=meta.get("category"),
        license=meta.get("license"),
        source=meta.get("source"),
        scope=meta["scope"],
        params=[TemplateParamOut(**p) for p in meta.get("params") or []],
    )
