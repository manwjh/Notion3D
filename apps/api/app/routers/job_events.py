"""Job SSE stream endpoint."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.deps import ProjectDep
from app.services import job_events, job_service
from app.services.job_present import job_to_out

router = APIRouter(prefix="/api/projects", tags=["jobs"])


def _serialize_job(job: dict) -> str:
    return json.dumps(job_to_out(job).model_dump(mode="json"), ensure_ascii=False)


@router.get("/{project_id}/jobs/{job_id}/events")
async def stream_job_events(project: ProjectDep, job_id: str) -> StreamingResponse:
    job = job_service.get_job(job_id)
    if not job or job["project_id"] != project.id:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def event_generator():
        queue = job_events.subscribe(job_id)
        try:
            current = job_service.get_job(job_id)
            if not current:
                return
            yield f"data: {_serialize_job(current)}\n\n"
            if current.get("status") in ("succeeded", "failed"):
                return

            while True:
                try:
                    updated = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue

                yield f"data: {_serialize_job(updated)}\n\n"
                if updated.get("status") in ("succeeded", "failed"):
                    break
        finally:
            job_events.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
