"""Chat message and agent status presentation."""

from __future__ import annotations

from datetime import datetime

from app.models.schemas import AgentStatusOut, ChatMessageOut, MessageRole
from app.services import design_turn, storage, turn_service


def messages_out(project_id: str) -> list[ChatMessageOut]:
    return [
        ChatMessageOut(
            id=m["id"],
            role=MessageRole(m["role"]),
            content=m["content"],
            created_at=datetime.fromisoformat(m["created_at"]),
            turn_id=m.get("turn_id"),
            job_id=m.get("job_id"),
        )
        for m in storage.list_messages(project_id)
    ]


def agent_status_out(project_id: str) -> AgentStatusOut:
    meta = storage.load_meta(project_id)
    pending = meta.get("agent_run_pending")
    active_job = turn_service.active_job_for_project(project_id)
    active_job_id = active_job["id"] if active_job else None
    active_turn = design_turn.get_active_turn(project_id)
    turn_id = active_turn["id"] if active_turn else None

    if not pending:
        return AgentStatusOut(
            active=False,
            turn_id=turn_id,
            active_job_id=active_job_id,
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
    )
