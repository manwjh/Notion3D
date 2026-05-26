"""Design pipeline artifacts — plan & review for active turns."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import ProjectDep
from app.models.schemas import DesignArtifactOut, DesignPlanIn, DesignReviewIn, DesignPhase
from app.services import design_turn

router = APIRouter(prefix="/api/projects", tags=["design"])


@router.post("/{project_id}/design/plan", response_model=DesignArtifactOut)
async def submit_design_plan(project: ProjectDep, body: DesignPlanIn) -> DesignArtifactOut:
    turn = design_turn.set_design_plan(
        project.id,
        body.turn_id,
        body.model_dump(exclude={"turn_id"}, mode="json"),
    )
    return _artifact_out(turn)


@router.post("/{project_id}/design/review", response_model=DesignArtifactOut)
async def submit_design_review(project: ProjectDep, body: DesignReviewIn) -> DesignArtifactOut:
    turn = design_turn.set_design_review(
        project.id,
        body.turn_id,
        status=body.status.value,
        notes=body.notes,
        retry_phase=body.retry_phase.value if body.retry_phase else None,
    )
    return _artifact_out(turn)


@router.get("/{project_id}/design/state", response_model=DesignArtifactOut | None)
async def get_design_state(project: ProjectDep) -> DesignArtifactOut | None:
    turn = design_turn.get_active_turn(project.id)
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
