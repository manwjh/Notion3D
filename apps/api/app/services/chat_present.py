"""Chat message and agent status presentation."""

from __future__ import annotations

from datetime import datetime

from app.models.schemas import AgentStatusOut, ChatMessageOut, MessageRole
from app.services import design_turn, storage, turn_service


def messages_out(project_id: str) -> list[ChatMessageOut]:
    from app.models.schemas import ChatImageOut

    result: list[ChatMessageOut] = []
    for m in storage.list_messages(project_id):
        images = [
            ChatImageOut(
                id=img.get("id") or str(i),
                url=img.get("url") or "",
                mime_type=img.get("mime_type") or "image/png",
                filename=img.get("filename"),
            )
            for i, img in enumerate(m.get("images") or [])
            if img.get("url")
        ]
        result.append(
            ChatMessageOut(
                id=m["id"],
                role=MessageRole(m["role"]),
                content=m["content"],
                created_at=datetime.fromisoformat(m["created_at"]),
                turn_id=m.get("turn_id"),
                job_id=m.get("job_id"),
                images=images,
            )
        )
    return result


def agent_status_out(project_id: str) -> AgentStatusOut:
    from app.models.schemas import AgentActivityStepOut

    meta = storage.load_meta(project_id)
    pending = meta.get("agent_run_pending")
    active_job = turn_service.active_job_for_project(project_id)
    active_job_id = active_job["id"] if active_job else None
    active_turn = design_turn.get_active_turn(project_id)
    turn_id = active_turn["id"] if active_turn else None
    raw_activity = list(meta.get("agent_activity") or [])
    activity = [
        AgentActivityStepOut(
            id=str(step.get("id") or i),
            kind=str(step.get("kind") or "tool"),
            label=str(step.get("label") or "…"),
            detail=step.get("detail"),
            status=str(step.get("status") or "running"),
            tool=step.get("tool"),
            at=step.get("at"),
        )
        for i, step in enumerate(raw_activity)
        if isinstance(step, dict)
    ]

    if not pending:
        return AgentStatusOut(
            active=False,
            turn_id=turn_id,
            active_job_id=active_job_id,
            activity=activity,
        )

    return AgentStatusOut(
        active=True,
        turn_id=pending.get("turn_id") or turn_id,
        provider=pending.get("provider"),
        session_id=pending.get("session_id"),
        run_id=pending.get("run_id"),
        status="RUNNING",
        external_url=pending.get("external_url"),
        active_job_id=active_job_id,
        activity=activity,
    )
