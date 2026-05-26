"""Build unified project snapshots for Web state + SSE."""

from __future__ import annotations

from app.models.schemas import ProjectCapabilitiesOut, ProjectStateOut
from app.services import design_turn, storage, turn_service
from app.services.capabilities import capabilities_async as project_capabilities_async
from app.services.chat_present import agent_status_out, messages_out
from app.services.job_present import job_to_out
from app.services.web_turn_config import WEB_TURN_BRIDGE


async def build_project_state_out(project_id: str) -> ProjectStateOut | None:
    project = storage.get_project(project_id)
    if not project:
        return None

    from app.services import agent_activity

    meta = storage.load_meta(project_id)
    pending = meta.get("agent_run_pending")
    if pending and pending.get("provider") == WEB_TURN_BRIDGE and pending.get("run_id"):
        run = await agent_activity.fetch_bridge_run(pending["run_id"])
        status = str(run.get("status") or "").upper()
        if status in ("FINISHED", "ERROR"):
            await agent_activity.heal_stale_agent_pending(project_id, pending, run)

    active_job = turn_service.active_job_for_project(project_id)
    agent = agent_status_out(project_id)
    caps = await project_capabilities_async(agent_active=agent.active)

    return ProjectStateOut(
        project=project,
        messages=messages_out(project_id),
        active_turn=design_turn.turn_out(project_id, active_job),
        active_job=job_to_out(active_job) if active_job else None,
        agent=agent,
        capabilities=ProjectCapabilitiesOut(**caps),
    )
