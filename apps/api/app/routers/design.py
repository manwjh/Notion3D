"""Design pipeline artifacts — plan & review for active turns."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import DesignArtifactOut, DesignPlanIn, DesignReviewIn, DesignPhase
from app.services import design_turn, storage

router = APIRouter(prefix="/api/projects", tags=["design"])


@router.post("/{project_id}/design/plan", response_model=DesignArtifactOut)
async def submit_design_plan(project_id: str, body: DesignPlanIn) -> DesignArtifactOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        turn = design_turn.set_design_plan(
            project_id,
            body.turn_id,
            body.model_dump(exclude={"turn_id"}, mode="json"),
        )
    except design_turn.DesignTurnError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _artifact_out(turn)


@router.post("/{project_id}/design/review", response_model=DesignArtifactOut)
async def submit_design_review(project_id: str, body: DesignReviewIn) -> DesignArtifactOut:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        turn = design_turn.set_design_review(
            project_id,
            body.turn_id,
            status=body.status.value,
            notes=body.notes,
            retry_phase=body.retry_phase.value if body.retry_phase else None,
        )
    except design_turn.DesignTurnError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _artifact_out(turn)


@router.get("/{project_id}/design/state", response_model=DesignArtifactOut | None)
async def get_design_state(project_id: str) -> DesignArtifactOut | None:
    if not storage.get_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    turn = design_turn.get_active_turn(project_id)
    if not turn:
        return None
    return _artifact_out(turn)


def _artifact_out(turn: dict) -> DesignArtifactOut:
    return DesignArtifactOut(
        turn_id=turn["id"],
        design_phase=DesignPhase(turn.get("design_phase", DesignPhase.intake.value)),
        plan=turn.get("plan"),
        review=turn.get("review"),
        revision=turn.get("revision") or 0,
    )
