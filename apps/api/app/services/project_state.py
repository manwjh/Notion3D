"""Build unified project snapshots for Web state + SSE."""

from __future__ import annotations

from app.models.schemas import ProjectCapabilitiesOut, ProjectStateOut
from app.services import design_turn, storage, turn_service
from app.services.capabilities import capabilities_async as project_capabilities_async
from app.services.chat_present import agent_status_out, messages_out
from app.services.job_present import job_to_out


async def build_project_state_out(project_id: str) -> ProjectStateOut | None:
    project = storage.get_project(project_id)
    if not project:
        return None

    active_job = turn_service.active_job_for_project(project_id)
    caps = await project_capabilities_async()

    return ProjectStateOut(
        project=project,
        messages=messages_out(project_id),
        active_turn=design_turn.turn_out(project_id, active_job),
        active_job=job_to_out(active_job) if active_job else None,
        agent=agent_status_out(project_id),
        capabilities=ProjectCapabilitiesOut(**caps),
    )
