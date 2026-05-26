from datetime import datetime
import logging
import re

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, Response

from app.deps import ProjectDep
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
    TemplateOut,
    TemplateParamOut,
    VersionStatus,
)
from app.services.cad_backend import CadBackend
from app.services import (
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
    return VersionStatus.pending


def _version_created_at(out_dir) -> datetime:
    stl = out_dir / "model.stl"
    if stl.exists():
        return datetime.fromtimestamp(stl.stat().st_mtime)
    forge = out_dir / "model.forge.js"
    if forge.exists():
        return datetime.fromtimestamp(forge.stat().st_mtime)
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
async def get_project(project: ProjectDep) -> ProjectOut:
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str) -> None:
    if not storage.delete_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")


@router.get("/{project_id}/messages", response_model=list[ChatMessageOut])
async def list_messages(project: ProjectDep) -> list[ChatMessageOut]:
    return chat_present.messages_out(project.id)


@router.post("/{project_id}/render-forge", response_model=JobOut)
async def render_forge(
    project: ProjectDep,
    body: ForgeRenderIn,
    background_tasks: BackgroundTasks,
) -> JobOut:
    forge_code = forgecad_service.prepare_forge(body.forge_code)

    source = body.source.value
    turn_id = design_turn.active_turn_id(project.id) if source == JobSource.agent.value else None

    job = job_service.create_render_job(
        project.id,
        forge_code,
        body.label,
        turn_id=turn_id,
        source=source,
        forge_files=body.files,
    )
    static_warnings = forgecad_service.static_forge_warnings(forge_code, body.files)
    if static_warnings:
        job_service.update_job(job["id"], validation_warnings=static_warnings)
        job = job_service.get_job(job["id"]) or job
    if turn_id:
        design_turn.register_job(project.id, turn_id, job["id"], prompt=body.label)
    background_tasks.add_task(job_service.run_render_job, job["id"])
    return _job_to_out(job)


@router.get("/{project_id}/jobs/active", response_model=list[JobOut])
async def list_active_jobs(project: ProjectDep) -> list[JobOut]:
    return [_job_to_out(job) for job in job_store.list_active_jobs(project.id)]


@router.get("/{project_id}/jobs/{job_id}", response_model=JobOut)
async def get_job(project: ProjectDep, job_id: str) -> JobOut:
    job = job_service.get_job(job_id)
    if not job or job["project_id"] != project.id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _job_to_out(job)


@router.get("/{project_id}/versions", response_model=list[ModelVersionOut])
async def list_versions(project: ProjectDep) -> list[ModelVersionOut]:
    versions: list[ModelVersionOut] = []
    if not project.latest_version:
        return versions

    for v in range(1, project.latest_version + 1):
        out_dir = storage.version_dir(project.id, v)
        forge = out_dir / "model.forge.js"
        stl = out_dir / "model.stl"
        if not forge.exists() and not stl.exists():
            continue
        versions.append(_version_out(project.id, v, out_dir))
    return versions


@router.post("/{project_id}/versions/{version}/resume-stl", response_model=JobOut)
async def resume_version_stl(
    project: ProjectDep,
    version: int,
    background_tasks: BackgroundTasks,
) -> JobOut:
    job = await job_service.resume_version_stl(project.id, version)
    background_tasks.add_task(job_service.run_render_job, job["id"])
    return _job_to_out(job)


@router.get("/{project_id}/versions/{version}/parts.json")
async def download_parts_manifest(project: ProjectDep, version: int):
    path = storage.version_dir(project.id, version) / "parts.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="部件清单不存在")
    import json

    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/{project_id}/versions/{version}/parts/{part_id}.stl")
async def download_part_stl(project: ProjectDep, version: int, part_id: str) -> FileResponse:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", part_id):
        raise HTTPException(status_code=400, detail="无效的部件 ID")
    path = storage.version_dir(project.id, version) / "parts" / f"{part_id}.stl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="部件 STL 不存在")
    return FileResponse(path, media_type="model/stl", filename=f"{part_id}_v{version}.stl")


@router.get("/{project_id}/versions/{version}/model.stl")
async def download_stl(project: ProjectDep, version: int) -> FileResponse:
    path = storage.version_dir(project.id, version) / "model.stl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="STL 不存在")
    return FileResponse(path, media_type="model/stl", filename=f"model_v{version}.stl")


@router.post("/{project_id}/versions/{version}/forge-preview", response_model=ForgePreviewOut)
async def start_forge_preview(project: ProjectDep, version: int) -> ForgePreviewOut:
    result = await forge_preview_service.ensure_preview(project.id, version)
    if not result.get("ready"):
        raise HTTPException(status_code=503, detail=result.get("error") or "预览不可用")
    return ForgePreviewOut(**result)


@router.get("/{project_id}/versions/{version}/forge-sources", response_model=ForgeSourcesOut)
async def get_forge_sources(project: ProjectDep, version: int) -> ForgeSourcesOut:
    out_dir = storage.version_dir(project.id, version)
    sources = forgecad_service.read_forge_sources(out_dir)
    meta = _version_meta(out_dir)
    return ForgeSourcesOut(
        version=version,
        forge_code=str(sources["forge_code"]),
        files=dict(sources["files"]),
        cad_backend=meta.get("cad_backend") or CadBackend.forgecad.value,
    )


@router.get("/{project_id}/versions/{version}/src/{file_path:path}")
async def download_forge_src(project: ProjectDep, version: int, file_path: str) -> FileResponse:
    out_dir = storage.version_dir(project.id, version)
    content = forgecad_service.read_src_file(out_dir, file_path)
    rel = file_path.strip().lstrip("/").replace("\\", "/")
    filename = rel.replace("/", "_")
    return Response(
        content=content,
        media_type="text/javascript",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/{project_id}/versions/{version}/model.forge.js")
async def download_forge(project: ProjectDep, version: int) -> FileResponse:
    path = storage.version_dir(project.id, version) / "model.forge.js"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Forge 源码不存在")
    return FileResponse(path, media_type="text/javascript", filename=f"model_v{version}.forge.js")


@router.post("/{project_id}/versions/{version}/save-template", response_model=TemplateOut)
async def save_version_as_template(
    project: ProjectDep,
    version: int,
    body: SaveTemplateIn,
) -> TemplateOut:
    forge_path = storage.version_dir(project.id, version) / "model.forge.js"
    if not forge_path.exists():
        raise HTTPException(status_code=404, detail="该版本尚无 Forge 源码")

    forge_code = forge_path.read_text(encoding="utf-8")
    meta = await template_library.save_user_forge_template_validated(
        template_id=body.id,
        title=body.title,
        forge_code=forge_code,
        description=body.description,
        tags=body.tags,
        category=body.category,
        derived_from={
            "project_id": project.id,
            "version": version,
        },
    )

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
