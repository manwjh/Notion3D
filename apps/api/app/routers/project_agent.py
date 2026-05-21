"""Web design conversation — unified turn + project state."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.schemas import (
    AgentStatusOut,
    AgentTurnIn,
    ProjectCapabilitiesOut,
    ProjectStateOut,
    TurnOut,
)
from app.services import storage
from app.services.capabilities import capabilities as project_capabilities
from app.services.chat_present import agent_status_out, messages_out
from app.services.job_present import job_to_out
from app.services import turn_service

router = APIRouter(prefix="/api/projects", tags=["design"])


def _start_agent(project_id: str, pending: dict, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(turn_service.finish_agent_run, project_id, pending)


@router.post("/{project_id}/turn", response_model=TurnOut)
async def design_turn(
    project_id: str,
    body: AgentTurnIn,
    background_tasks: BackgroundTasks,
) -> TurnOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")

    def start_agent(pid: str, pending: dict) -> None:
        _start_agent(pid, pending, background_tasks)

    return await turn_service.handle_turn(
        project_id,
        body,
        start_agent_turn=start_agent,
    )


@router.get("/{project_id}/agent/status", response_model=AgentStatusOut)
async def agent_status(project_id: str) -> AgentStatusOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return agent_status_out(project_id)


@router.get("/{project_id}/state", response_model=ProjectStateOut)
async def project_state(project_id: str) -> ProjectStateOut:
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    active_job = turn_service.active_job_for_project(project_id)
    caps = project_capabilities()

    return ProjectStateOut(
        project=project,
        messages=messages_out(project_id),
        active_job=job_to_out(active_job) if active_job else None,
        agent=agent_status_out(project_id),
        capabilities=ProjectCapabilitiesOut(**caps),
    )
