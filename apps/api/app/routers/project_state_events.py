"""Project state SSE stream."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.deps import ProjectDep
from app.services import project_events, project_state

router = APIRouter(prefix="/api/projects", tags=["design"])


def _serialize_state(state) -> str:
    return json.dumps(state.model_dump(mode="json"), ensure_ascii=False)


@router.get("/{project_id}/state/events")
async def stream_project_state(project: ProjectDep) -> StreamingResponse:
    project_id = project.id

    async def event_generator():
        queue = project_events.subscribe(project_id)
        try:
            while True:
                snapshot = await project_state.build_project_state_out(project_id)
                if snapshot is None:
                    return
                yield f"data: {_serialize_state(snapshot)}\n\n"
                if not snapshot.agent.active:
                    return

                try:
                    await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            project_events.unsubscribe(project_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
