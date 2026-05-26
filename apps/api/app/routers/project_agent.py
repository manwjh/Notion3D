"""Web design conversation — unified turn + project state."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.deps import ProjectDep
from app.models.schemas import AgentStatusOut, AgentTurnIn, TurnOut
from app.services.chat_present import agent_status_out
from app.services.project_state import build_project_state_out
from app.services import turn_service

router = APIRouter(prefix="/api/projects", tags=["design"])


def _start_agent(project_id: str, pending: dict, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(turn_service.finish_agent_run, project_id, pending)


@router.post("/{project_id}/turn", response_model=TurnOut)
async def submit_turn(
    project: ProjectDep,
    body: AgentTurnIn,
    background_tasks: BackgroundTasks,
) -> TurnOut:
    def start_agent(pid: str, pending: dict) -> None:
        _start_agent(pid, pending, background_tasks)

    return await turn_service.handle_turn(
        project.id,
        body,
        start_agent_turn=start_agent,
    )


@router.get("/{project_id}/agent/status", response_model=AgentStatusOut)
async def agent_status(project: ProjectDep) -> AgentStatusOut:
    return agent_status_out(project.id)


@router.get("/{project_id}/state")
async def project_state(project: ProjectDep):
    return await build_project_state_out(project.id)
