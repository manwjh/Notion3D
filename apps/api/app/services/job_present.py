"""Map internal job dicts to API responses for Web + MCP."""

from __future__ import annotations

from datetime import datetime

from app.models.schemas import JobOut, JobStatus
from app.services.links import project_web_url


def job_phase(job: dict) -> str:
    status = job.get("status")
    if status == JobStatus.failed.value:
        return "failed"
    if status == JobStatus.succeeded.value:
        return "done"
    if job.get("stl_ready") or job.get("checkpoint") == "stl_done":
        return "stl"
    if job.get("preview_ready") or job.get("checkpoint") == "preview_done":
        return "preview"
    if job.get("checkpoint") in ("scad_ready", "version_created"):
        return "scad"
    if status == JobStatus.running.value:
        return "scad"
    return "pending"


def job_to_out(job: dict) -> JobOut:
    project_id = job["project_id"]
    status = JobStatus(job["status"])
    phase = job_phase(job)
    error = job.get("message") if status == JobStatus.failed else None
    return JobOut(
        id=job["id"],
        project_id=project_id,
        kind=job.get("kind"),
        status=status,
        phase=phase,
        prompt=job.get("prompt"),
        message=job.get("message"),
        version=job.get("version"),
        preview_url=job.get("preview_url"),
        preview_ready=bool(job.get("preview_ready")),
        stl_ready=bool(job.get("stl_ready")),
        error=error,
        created_at=datetime.fromisoformat(job["created_at"]),
        updated_at=datetime.fromisoformat(job["updated_at"]),
        web_url=project_web_url(project_id),
    )
