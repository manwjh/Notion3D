from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import (
    ActionResult,
    ChatMessageIn,
    ChatMessageOut,
    GenerateRequest,
    JobOut,
    MessageRole,
    ModelVersionOut,
    ProjectCreate,
    ProjectOut,
    ScadRenderIn,
    VersionStatus,
)
from app.services import cad_service, job_service, job_store, print_service, slicer_service, storage
from app.services.links import project_web_url

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _version_meta(out_dir) -> dict:
    meta_file = out_dir / "meta.json"
    if not meta_file.exists():
        return {}
    import json

    return json.loads(meta_file.read_text(encoding="utf-8"))


def _save_version_meta(out_dir, meta: dict) -> None:
    import json

    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _version_status(out_dir, meta: dict) -> VersionStatus:
    if meta.get("status") == "complete" or (out_dir / "model.stl").exists():
        return VersionStatus.complete
    if meta.get("status") == "preview_ready" or (out_dir / "preview.png").exists():
        return VersionStatus.preview_ready
    if (out_dir / "model.scad").exists():
        return VersionStatus.pending
    return VersionStatus.pending


def _version_created_at(out_dir) -> datetime:
    stl = out_dir / "model.stl"
    if stl.exists():
        return datetime.fromtimestamp(stl.stat().st_mtime)
    scad = out_dir / "model.scad"
    if scad.exists():
        return datetime.fromtimestamp(scad.stat().st_mtime)
    return datetime.fromtimestamp(out_dir.stat().st_mtime)


def _version_out(project_id: str, v: int, out_dir) -> ModelVersionOut:
    stl = out_dir / "model.stl"
    meta = _version_meta(out_dir)
    status = _version_status(out_dir, meta)
    three_mf = out_dir / "model.gcode.3mf"
    if not three_mf.exists():
        three_mf = out_dir / "model.3mf"
    return ModelVersionOut(
        version=v,
        status=status,
        stl_url=(
            f"/api/projects/{project_id}/versions/{v}/model.stl"
            if stl.exists()
            else None
        ),
        scad_url=(
            f"/api/projects/{project_id}/versions/{v}/model.scad"
            if (out_dir / "model.scad").exists()
            else None
        ),
        preview_url=(
            f"/api/projects/{project_id}/versions/{v}/preview.png"
            if (out_dir / "preview.png").exists()
            else None
        ),
        three_mf_url=(
            f"/api/projects/{project_id}/versions/{v}/print.3mf"
            if three_mf.exists()
            else None
        ),
        created_at=_version_created_at(out_dir),
        prompt=meta.get("prompt"),
    )


def _job_out(job: dict) -> JobOut:
    project_id = job["project_id"]
    return JobOut(
        id=job["id"],
        project_id=project_id,
        status=job["status"],
        prompt=job.get("prompt"),
        message=job.get("message"),
        version=job.get("version"),
        preview_url=job.get("preview_url"),
        preview_ready=bool(job.get("preview_ready")),
        stl_ready=bool(job.get("stl_ready")),
        created_at=datetime.fromisoformat(job["created_at"]),
        updated_at=datetime.fromisoformat(job["updated_at"]),
        web_url=project_web_url(project_id),
    )


@router.get("", response_model=list[ProjectOut])
async def list_projects() -> list[ProjectOut]:
    return storage.list_projects()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate) -> ProjectOut:
    return storage.create_project(body.name, tool=body.tool)


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
    return [
        ChatMessageOut(
            id=m["id"],
            role=MessageRole(m["role"]),
            content=m["content"],
            created_at=datetime.fromisoformat(m["created_at"]),
            job_id=m.get("job_id"),
        )
        for m in storage.list_messages(project_id)
    ]


@router.post("/{project_id}/chat", response_model=JobOut)
async def chat_and_generate(
    project_id: str,
    body: ChatMessageIn,
    background_tasks: BackgroundTasks,
) -> JobOut:
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    user_text = body.content
    if body.region:
        user_text = f"{body.content}\n\n📍 部位：{body.region}"
    elif body.pick:
        label = body.pick.label or f"({body.pick.x:.1f}, {body.pick.y:.1f}, {body.pick.z:.1f})"
        user_text = f"{body.content}\n\n📍 3D 点选：{label}"

    storage.append_message(project_id, MessageRole.user, user_text)
    pick_data = body.pick.model_dump() if body.pick else None
    job = job_service.create_job(
        project_id, body.content, pick=pick_data, region=body.region
    )
    background_tasks.add_task(job_service.run_generate_job, job["id"])
    return _job_out(job)


@router.post("/{project_id}/render-scad", response_model=JobOut)
async def render_scad(
    project_id: str,
    body: ScadRenderIn,
    background_tasks: BackgroundTasks,
) -> JobOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    job = job_service.create_render_job(project_id, body.scad_code, body.label)
    background_tasks.add_task(job_service.run_render_scad_job, job["id"])
    return _job_out(job)


@router.post("/{project_id}/generate", response_model=JobOut)
async def generate(
    project_id: str,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> JobOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    job = job_service.create_job(project_id, body.prompt)
    background_tasks.add_task(job_service.run_generate_job, job["id"])
    return _job_out(job)


@router.get("/{project_id}/jobs/active", response_model=list[JobOut])
async def list_active_jobs(project_id: str) -> list[JobOut]:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return [_job_out(job) for job in job_store.list_active_jobs(project_id)]


@router.get("/{project_id}/jobs/{job_id}", response_model=JobOut)
async def get_job(project_id: str, job_id: str) -> JobOut:
    job = job_service.get_job(job_id)
    if not job or job["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _job_out(job)


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
        scad = out_dir / "model.scad"
        preview = out_dir / "preview.png"
        stl = out_dir / "model.stl"
        if not scad.exists() and not preview.exists() and not stl.exists():
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
    return _job_out(job)


@router.get("/{project_id}/versions/{version}/model.stl")
async def download_stl(project_id: str, version: int) -> FileResponse:
    path = storage.version_dir(project_id, version) / "model.stl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="STL 不存在")
    return FileResponse(path, media_type="model/stl", filename=f"model_v{version}.stl")


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


@router.post("/{project_id}/versions/{version}/slice", response_model=ActionResult)
async def slice_version(project_id: str, version: int) -> ActionResult:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    out_dir = storage.version_dir(project_id, version)
    stl_path = out_dir / "model.stl"
    if not stl_path.exists():
        raise HTTPException(status_code=404, detail="STL 不存在")

    three_mf_path = out_dir / "model.gcode.3mf"
    try:
        await slicer_service.slice_stl_to_3mf(stl_path, three_mf_path)
        meta = _version_meta(out_dir)
        meta["sliced"] = True
        _save_version_meta(out_dir, meta)
        storage.append_message(
            project_id,
            MessageRole.assistant,
            content=f"版本 v{version} 切片完成，可发送到拓竹打印。",
        )
        return ActionResult(
            ok=True,
            message="切片完成",
            three_mf_url=f"/api/projects/{project_id}/versions/{version}/print.3mf",
        )
    except slicer_service.SlicerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}/versions/{version}/print.3mf")
async def download_3mf(project_id: str, version: int) -> FileResponse:
    out_dir = storage.version_dir(project_id, version)
    for name in ("model.gcode.3mf", "model.3mf"):
        path = out_dir / name
        if path.exists():
            return FileResponse(
                path,
                media_type="application/3mf",
                filename=f"model_v{version}.gcode.3mf",
            )
    raise HTTPException(status_code=404, detail="3MF 不存在，请先切片")


@router.post("/{project_id}/versions/{version}/print", response_model=ActionResult)
async def print_version(project_id: str, version: int) -> ActionResult:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    out_dir = storage.version_dir(project_id, version)
    three_mf_path = out_dir / "model.gcode.3mf"
    if not three_mf_path.exists():
        three_mf_path = out_dir / "model.3mf"
    if not three_mf_path.exists():
        raise HTTPException(status_code=400, detail="请先切片生成 3MF")

    project = storage.get_project(project_id)
    name = f"{project.name if project else 'model'}_v{version}"
    try:
        url = print_service.send_to_bambu_connect(three_mf_path, name)
        storage.append_message(
            project_id,
            MessageRole.assistant,
            content=f"已发送到 Bambu Connect：{name}。请在 Bambu Connect 中确认并开始打印。",
        )
        return ActionResult(ok=True, message="已唤起 Bambu Connect", bambu_connect_url=url)
    except print_service.PrintError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
