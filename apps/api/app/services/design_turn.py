"""Design turn — links user intent, agent run, jobs, and versions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.models.schemas import DesignTurnOut, JobStatus
from app.services import storage


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def begin_turn(project_id: str, user_message_id: str, *, turn_id: str | None = None) -> str:
    tid = turn_id or str(uuid.uuid4())
    turn = {
        "id": tid,
        "user_message_id": user_message_id,
        "assistant_message_id": None,
        "job_id": None,
        "job_ids": [],
        "version": None,
        "agent_phase": "running",
        "render_phase": "idle",
        "created_at": _utcnow(),
    }
    storage.update_project_meta(project_id, active_turn=turn)
    return tid


def get_active_turn(project_id: str) -> dict | None:
    meta = storage.load_meta(project_id)
    return meta.get("active_turn")


def active_turn_id(project_id: str) -> str | None:
    turn = get_active_turn(project_id)
    return turn["id"] if turn else None


def _patch_turn(project_id: str, **fields) -> dict | None:
    turn = get_active_turn(project_id)
    if not turn:
        return None
    turn.update(fields)
    storage.update_project_meta(project_id, active_turn=turn)
    return turn


def register_job(project_id: str, turn_id: str, job_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    job_ids = list(turn.get("job_ids") or [])
    if job_id not in job_ids:
        job_ids.append(job_id)
    _patch_turn(
        project_id,
        job_id=job_id,
        job_ids=job_ids,
        render_phase="running",
    )


def set_version(project_id: str, turn_id: str, version: int) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    _patch_turn(project_id, version=version)


def set_agent_replied(project_id: str, turn_id: str, assistant_message_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    _patch_turn(
        project_id,
        assistant_message_id=assistant_message_id,
        agent_phase="replied",
    )
    maybe_finalize_turn(project_id)


def set_agent_failed(project_id: str, turn_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    _patch_turn(project_id, agent_phase="failed")
    maybe_finalize_turn(project_id)


def sync_render_from_job(project_id: str, job: dict) -> None:
    turn_id = job.get("turn_id")
    if not turn_id:
        return
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return

    status = job.get("status")
    fields: dict = {}
    if status == JobStatus.failed.value:
        fields["render_phase"] = "failed"
    elif status == JobStatus.succeeded.value:
        fields["render_phase"] = "done"
        if job.get("version") is not None:
            fields["version"] = job["version"]
    elif status in (JobStatus.pending.value, JobStatus.running.value):
        fields["render_phase"] = "running"
        fields["job_id"] = job.get("id")
    else:
        return

    _patch_turn(project_id, **fields)
    if status in (JobStatus.succeeded.value, JobStatus.failed.value):
        maybe_finalize_turn(project_id)


def maybe_finalize_turn(project_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn:
        return

    agent_phase = turn.get("agent_phase", "running")
    render_phase = turn.get("render_phase", "idle")

    if agent_phase == "running":
        return
    if render_phase == "running":
        return

    storage.update_project_meta(project_id, active_turn=None)


def turn_out(project_id: str, active_job: dict | None = None) -> DesignTurnOut | None:
    if active_job:
        sync_render_from_job(project_id, active_job)
    turn = get_active_turn(project_id)
    if not turn:
        return None
    return DesignTurnOut(
        id=turn["id"],
        agent_phase=turn.get("agent_phase", "running"),
        render_phase=turn.get("render_phase", "idle"),
        user_message_id=turn["user_message_id"],
        assistant_message_id=turn.get("assistant_message_id"),
        job_id=turn.get("job_id"),
        version=turn.get("version"),
    )
