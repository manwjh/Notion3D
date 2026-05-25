import json
import uuid
from datetime import datetime, timezone

from app.models.schemas import JobSource, JobStatus, MessageRole
from app.services import cad_service, design_turn, forgecad_service, job_store, storage
from app.services.cad_backend import CadBackend, source_filename
from app.services.cad_service import CadError
from app.services.pick_context import format_edit_prompt

_jobs: dict[str, dict] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _persist(job: dict) -> dict:
    _jobs[job["id"]] = job
    job_store.save_job(job)
    return job


def _new_job(**fields) -> dict:
    now = _utcnow().isoformat()
    job = {
        "checkpoint": "pending",
        "message": None,
        "version": None,
        "preview_url": None,
        "preview_ready": False,
        "stl_ready": False,
        "scad_code": None,
        "forge_code": None,
        "forge_files": None,
        "cad_backend": CadBackend.forgecad.value,
        "turn_id": None,
        "source": JobSource.agent.value,
        "created_at": now,
        "updated_at": now,
        **fields,
    }
    return _persist(job)


def create_template_job(
    project_id: str,
    prompt: str,
    pick: dict | None = None,
    region: str | None = None,
) -> dict:
    return _new_job(
        id=str(uuid.uuid4()),
        project_id=project_id,
        prompt=prompt,
        pick=pick,
        region=region,
        kind="template",
        source=JobSource.template.value,
        status=JobStatus.pending.value,
    )


def create_render_job(
    project_id: str,
    source_code: str,
    label: str = "手动编辑",
    *,
    turn_id: str | None = None,
    source: str = JobSource.manual.value,
    backend: CadBackend = CadBackend.forgecad,
    forge_files: dict[str, str] | None = None,
) -> dict:
    fields: dict = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "prompt": label,
        "kind": "render",
        "turn_id": turn_id,
        "source": source,
        "status": JobStatus.pending.value,
        "cad_backend": backend.value,
        "forge_files": forge_files,
    }
    if backend == CadBackend.forgecad:
        fields["forge_code"] = source_code
    else:
        fields["scad_code"] = source_code
    return _new_job(**fields)


def load_jobs_from_disk() -> None:
    for job in job_store.list_all_jobs():
        _jobs[job["id"]] = job


def get_job(job_id: str) -> dict | None:
    job = _jobs.get(job_id)
    if job:
        return job
    job = job_store.load_job(job_id)
    if job:
        _jobs[job_id] = job
    return job


def update_job(job_id: str, **kwargs) -> dict | None:
    job = get_job(job_id)
    if not job:
        return None
    job.update(kwargs)
    job["updated_at"] = _utcnow().isoformat()
    return _persist(job)


def _version_meta_path(project_id: str, version: int):
    return storage.version_dir(project_id, version) / "meta.json"


def _read_version_meta(project_id: str, version: int) -> dict:
    meta_path = _version_meta_path(project_id, version)
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _write_version_meta(project_id: str, version: int, meta: dict) -> None:
    meta_path = _version_meta_path(project_id, version)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _snapshot_design_artifacts(project_id: str, job_id: str, version: int) -> None:
    job = get_job(job_id)
    if not job or not job.get("turn_id"):
        return
    turn = design_turn.get_active_turn(project_id)
    if not turn or turn["id"] != job["turn_id"]:
        return
    meta = _read_version_meta(project_id, version)
    if turn.get("plan"):
        meta["design_plan"] = turn["plan"]
    if turn.get("review"):
        meta["design_review"] = turn["review"]
    meta["design_revision"] = turn.get("revision") or 0
    _write_version_meta(project_id, version, meta)


def _set_version_status(project_id: str, version: int, status: str) -> None:
    meta = _read_version_meta(project_id, version)
    meta["status"] = status
    meta["version"] = version
    _write_version_meta(project_id, version, meta)


def _preview_api(project_id: str, version: int) -> str:
    return f"/api/projects/{project_id}/versions/{version}/preview.png"


async def _ensure_version_files(
    project_id: str,
    job_id: str,
    prompt: str,
    source_code: str,
    *,
    backend: CadBackend = CadBackend.forgecad,
) -> int:
    job = get_job(job_id)
    if not job:
        raise cad_service.CadError("任务不存在")

    if job.get("version"):
        version = job["version"]
    else:
        version = storage.next_version(project_id)
        update_job(job_id, version=version, checkpoint="version_created")

    out_dir = storage.version_dir(project_id, version)
    source_name = source_filename(backend)
    (out_dir / source_name).write_text(source_code, encoding="utf-8")

    meta = _read_version_meta(project_id, version)
    job = get_job(job_id)
    meta.update({
        "prompt": prompt,
        "version": version,
        "status": meta.get("status", "pending"),
        "turn_id": job.get("turn_id") if job else None,
        "job_id": job_id,
        "cad_backend": backend.value,
    })
    _write_version_meta(project_id, version, meta)
    return version


async def _render_preview_stage(
    project_id: str,
    job_id: str,
    version: int,
    scad_code: str,
) -> bool:
    out_dir = storage.version_dir(project_id, version)
    preview_path = out_dir / "preview.png"

    if preview_path.exists():
        update_job(
            job_id,
            preview_url=_preview_api(project_id, version),
            preview_ready=True,
            stl_ready=False,
            checkpoint="preview_done",
        )
        _set_version_status(project_id, version, "preview_ready")
        return True

    update_job(job_id, message="正在生成预览图…", version=version)
    await cad_service.render_preview_png(scad_code, preview_path)

    if preview_path.exists():
        update_job(
            job_id,
            message="预览图已就绪，正在计算 3D 网格…",
            preview_url=_preview_api(project_id, version),
            preview_ready=True,
            stl_ready=False,
            checkpoint="preview_done",
        )
        _set_version_status(project_id, version, "preview_ready")
        return True

    update_job(job_id, message="正在计算 3D 网格…", preview_ready=False, checkpoint="preview_done")
    return False


async def _render_stl_stage(
    project_id: str,
    job_id: str,
    version: int,
    source_code: str,
    *,
    backend: CadBackend = CadBackend.forgecad,
    forge_files: dict[str, str] | None = None,
) -> bool:
    out_dir = storage.version_dir(project_id, version)
    stl_path = out_dir / "model.stl"

    if stl_path.exists():
        update_job(job_id, message="3D 模型已就绪", stl_ready=True, checkpoint="stl_done")
        _set_version_status(project_id, version, "complete")
        return True

    update_job(job_id, message="正在生成 3D 模型…", version=version)

    if backend == CadBackend.forgecad:
        result = await forgecad_service.render_forge(
            source_code,
            out_dir,
            project_id=project_id,
            version=version,
            extra_files=forge_files,
        )
    else:
        result = await cad_service.render_stl(source_code, stl_path)
        try:
            await cad_service.render_part_stls(
                source_code,
                out_dir,
                project_id=project_id,
                version=version,
            )
        except CadError:
            parts_manifest_path = out_dir / "parts.json"
            if parts_manifest_path.exists():
                parts_manifest_path.unlink()

    if result.warnings:
        meta = _read_version_meta(project_id, version)
        meta["validation_warnings"] = result.warnings
        _write_version_meta(project_id, version, meta)
        update_job(job_id, validation_warnings=result.warnings)
        _append_validation_warnings(project_id, job_id, result.warnings, get_job(job_id))
    update_job(job_id, message="3D 模型已就绪", stl_ready=True, checkpoint="stl_done")
    _set_version_status(project_id, version, "complete")
    _snapshot_design_artifacts(project_id, job_id, version)
    return stl_path.exists()


async def _save_version(
    project_id: str,
    job_id: str,
    prompt: str,
    source_code: str,
    *,
    backend: CadBackend = CadBackend.forgecad,
    forge_files: dict[str, str] | None = None,
) -> int:
    version = await _ensure_version_files(
        project_id,
        job_id,
        prompt,
        source_code,
        backend=backend,
    )
    await _render_stl_stage(
        project_id,
        job_id,
        version,
        source_code,
        backend=backend,
        forge_files=forge_files,
    )
    return version


def _append_render_failure(project_id: str, job_id: str, content: str, turn_id: str | None) -> None:
    if job_store.message_exists_for_job(project_id, job_id):
        return
    storage.append_message(
        project_id,
        role=MessageRole.system,
        content=content,
        turn_id=turn_id,
        job_id=job_id,
    )


def _append_validation_warnings(
    project_id: str,
    job_id: str,
    warnings: list[str],
    job: dict | None,
) -> None:
    if not warnings:
        return
    for msg in reversed(storage.list_messages(project_id)):
        if msg.get("job_id") != job_id:
            continue
        if msg.get("role") != MessageRole.system.value:
            continue
        if "模型校验提示" in msg.get("content", ""):
            return

    lines = "\n".join(f"- {w}" for w in warnings)
    storage.append_message(
        project_id,
        role=MessageRole.system,
        content=f"模型校验提示（仍可导出）：\n{lines}",
        turn_id=job.get("turn_id") if job else None,
        job_id=job_id,
    )


def _finalize_job(project_id: str, job_id: str, job: dict) -> None:
    design_turn.sync_render_from_job(project_id, job)


def _latest_complete_scad(project_id: str) -> str | None:
    project = storage.get_project(project_id)
    if not project or not project.latest_version:
        return None
    for version in range(project.latest_version, 0, -1):
        out_dir = storage.version_dir(project_id, version)
        stl = out_dir / "model.stl"
        scad = out_dir / "model.scad"
        if stl.exists() and scad.exists():
            return scad.read_text(encoding="utf-8")
    return None


async def run_template_job(job_id: str) -> None:
    job = get_job(job_id)
    if not job or job.get("kind") != "template":
        return

    project_id = job["project_id"]
    prompt = job["prompt"]
    pick = job.get("pick")
    region = job.get("region")
    effective_prompt = format_edit_prompt(prompt, pick, region)

    if job.get("status") not in (JobStatus.pending.value, JobStatus.running.value):
        return

    update_job(job_id, status=JobStatus.running.value, message="正在生成 OpenSCAD…")

    try:
        project = storage.get_project(project_id)
        if not project:
            raise cad_service.CadError("项目不存在")

        scad_code = job.get("scad_code")
        if not scad_code and job.get("version"):
            scad_path = storage.version_dir(project_id, job["version"]) / "model.scad"
            if scad_path.exists():
                scad_code = scad_path.read_text(encoding="utf-8")
                update_job(job_id, scad_code=scad_code, checkpoint="scad_ready")

        if not scad_code:
            existing_scad = _latest_complete_scad(project_id)

            scad_code = await cad_service.prompt_to_scad(
                effective_prompt,
                existing_scad,
                user_prompt=prompt,
                region=region,
            )
            update_job(job_id, scad_code=scad_code, checkpoint="scad_ready")

        version = await _save_version(
            project_id,
            job_id,
            prompt,
            scad_code,
            backend=CadBackend.openscad_legacy,
        )

        update_job(
            job_id,
            status=JobStatus.succeeded.value,
            message=f"已生成版本 v{version}",
            version=version,
            checkpoint="complete",
        )
        job = get_job(job_id)
        if job:
            _finalize_job(project_id, job_id, job)
    except Exception as exc:
        update_job(job_id, status=JobStatus.failed.value, message=str(exc))
        job = get_job(job_id)
        _append_render_failure(
            project_id,
            job_id,
            f"渲染未成功：{exc}",
            job.get("turn_id") if job else None,
        )
        if job:
            _finalize_job(project_id, job_id, job)


async def run_render_scad_job(job_id: str) -> None:
    job = get_job(job_id)
    if not job or job.get("kind") != "render":
        return

    project_id = job["project_id"]
    prompt = job["prompt"]
    backend = CadBackend(job.get("cad_backend") or CadBackend.forgecad.value)

    if job.get("status") not in (JobStatus.pending.value, JobStatus.running.value):
        return

    render_label = "正在渲染 ForgeCAD…" if backend == CadBackend.forgecad else "正在渲染 SCAD…"
    update_job(job_id, status=JobStatus.running.value, message=render_label)

    try:
        if not storage.get_project(project_id):
            raise cad_service.CadError("项目不存在")

        if backend == CadBackend.forgecad:
            source_code = job.get("forge_code") or ""
            source_name = "model.forge.js"
        else:
            source_code = job.get("scad_code") or ""
            source_name = "model.scad"

        if not source_code.strip() and job.get("version"):
            source_path = storage.version_dir(project_id, job["version"]) / source_name
            if source_path.exists():
                source_code = source_path.read_text(encoding="utf-8")

        if not source_code.strip():
            raise cad_service.CadError("建模源码不能为空")

        version = await _save_version(
            project_id,
            job_id,
            prompt,
            source_code,
            backend=backend,
            forge_files=job.get("forge_files"),
        )

        update_job(
            job_id,
            status=JobStatus.succeeded.value,
            message=f"已渲染版本 v{version}",
            version=version,
            checkpoint="complete",
        )
        job = get_job(job_id)
        if job:
            _finalize_job(project_id, job_id, job)
    except Exception as exc:
        update_job(job_id, status=JobStatus.failed.value, message=str(exc))
        job = get_job(job_id)
        _append_render_failure(
            project_id,
            job_id,
            f"渲染未成功：{exc}",
            job.get("turn_id") if job else None,
        )
        if job:
            _finalize_job(project_id, job_id, job)


async def run_render_forge_job(job_id: str) -> None:
    """Alias for run_render_scad_job — forge is the default backend."""
    await run_render_scad_job(job_id)


async def resume_version_stl(project_id: str, version: int) -> dict:
    out_dir = storage.version_dir(project_id, version)
    meta = _read_version_meta(project_id, version)
    backend = CadBackend(meta.get("cad_backend") or CadBackend.forgecad.value)
    source_name = source_filename(backend)
    source_path = out_dir / source_name
    stl_path = out_dir / "model.stl"

    if not source_path.exists():
        raise cad_service.CadError("建模源码不存在")
    if stl_path.exists():
        raise cad_service.CadError("STL 已存在")

    existing = job_store.find_active_job_for_version(project_id, version)
    if existing:
        return existing

    source_code = source_path.read_text(encoding="utf-8")
    label = meta.get("prompt") or f"恢复 v{version} STL"
    forge_files = (
        forgecad_service.collect_src_files(out_dir)
        if backend == CadBackend.forgecad
        else None
    )

    job = create_render_job(
        project_id,
        source_code,
        label=f"恢复 v{version} STL",
        backend=backend,
        forge_files=forge_files or None,
    )
    preview_path = out_dir / "preview.png"
    update_job(
        job["id"],
        version=version,
        preview_ready=preview_path.exists(),
        preview_url=_preview_api(project_id, version) if preview_path.exists() else None,
        checkpoint="preview_done" if preview_path.exists() else "version_created",
        message="恢复计算 3D 网格…",
    )
    return get_job(job["id"]) or job


async def resume_interrupted_jobs() -> None:
    import asyncio

    for job in job_store.list_active_jobs():
        job_id = job["id"]
        if job.get("kind") == "template":
            asyncio.create_task(run_template_job(job_id))
        elif job.get("kind") == "render":
            asyncio.create_task(run_render_scad_job(job_id))

    for project in storage.list_projects():
        if not project.latest_version:
            continue
        for version in range(1, project.latest_version + 1):
            out_dir = storage.version_dir(project.id, version)
            stl_path = out_dir / "model.stl"
            forge_path = out_dir / "model.forge.js"
            scad_path = out_dir / "model.scad"
            if stl_path.exists() or (not forge_path.exists() and not scad_path.exists()):
                continue
            if job_store.find_active_job_for_version(project.id, version):
                continue

            prior = job_store.find_job_for_version(project.id, version)
            if prior and prior.get("status") in ("succeeded", "failed"):
                continue

            meta = _read_version_meta(project.id, version)
            status = meta.get("status", "pending")
            if status == "complete":
                continue

            backend = CadBackend(meta.get("cad_backend") or CadBackend.forgecad.value)
            source_name = source_filename(backend)
            source_path = out_dir / source_name
            if not source_path.exists():
                continue
            source_code = source_path.read_text(encoding="utf-8")
            forge_files = (
                forgecad_service.collect_src_files(out_dir)
                if backend == CadBackend.forgecad
                else None
            )
            job = create_render_job(
                project.id,
                source_code,
                label=f"恢复 v{version}",
                backend=backend,
                forge_files=forge_files or None,
            )
            preview_path = out_dir / "preview.png"
            update_job(
                job["id"],
                version=version,
                preview_ready=preview_path.exists(),
                preview_url=_preview_api(project.id, version) if preview_path.exists() else None,
                checkpoint="preview_done" if preview_path.exists() else "version_created",
                message="恢复未完成版本…",
            )
            asyncio.create_task(run_render_scad_job(job["id"]))
