"""Design turn — links user intent, agent phases, jobs, and versions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import DesignPhase, DesignTurnOut, JobStatus, MessageRole, PlanStrategy, ReviewStatus, TaskClass
from app.services import storage

TERMINAL_DESIGN_PHASES = frozenset({DesignPhase.done.value, DesignPhase.blocked.value})
MAX_DESIGN_REVISION = 2


class DesignTurnError(Exception):
    pass


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
        "design_phase": DesignPhase.intake.value,
        "plan": None,
        "review": None,
        "revision": 0,
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


def _resolve_turn(project_id: str, turn_id: str | None) -> dict:
    turn = get_active_turn(project_id)
    if not turn:
        raise DesignTurnError("当前没有进行中的设计轮次")
    if turn_id and turn["id"] != turn_id:
        raise DesignTurnError("turn_id 与当前 active_turn 不一致")
    return turn


def register_job(
    project_id: str,
    turn_id: str,
    job_id: str,
    *,
    prompt: str | None = None,
) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    ensure_implicit_plan(project_id, turn_id, prompt)
    job_ids = list(turn.get("job_ids") or [])
    if job_id not in job_ids:
        job_ids.append(job_id)
    _patch_turn(
        project_id,
        job_id=job_id,
        job_ids=job_ids,
        render_phase="running",
        design_phase=DesignPhase.render.value,
    )


def set_version(project_id: str, turn_id: str, version: int) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    _patch_turn(project_id, version=version)


def set_design_plan(project_id: str, turn_id: str | None, plan: dict[str, Any]) -> dict:
    turn = _resolve_turn(project_id, turn_id)
    if turn.get("design_phase") == DesignPhase.blocked.value:
        raise DesignTurnError("当前轮次已阻塞，无法提交计划")
    task_class = plan.get("task_class")
    strategy = plan.get("strategy")
    if task_class == TaskClass.C.value:
        next_phase = DesignPhase.blocked.value
    elif strategy == PlanStrategy.chat_only.value:
        next_phase = DesignPhase.done.value
    else:
        next_phase = DesignPhase.author.value
    stored = {
        **plan,
        "recorded_at": _utcnow(),
    }
    updated = _patch_turn(
        project_id,
        plan=stored,
        design_phase=next_phase,
    )
    return updated or turn


def set_design_review(
    project_id: str,
    turn_id: str | None,
    *,
    status: str,
    notes: list[str] | None = None,
    retry_phase: str | None = None,
) -> dict:
    turn = _resolve_turn(project_id, turn_id)
    review = {
        "status": status,
        "notes": notes or [],
        "retry_phase": retry_phase,
        "recorded_at": _utcnow(),
    }
    next_phase = DesignPhase.done.value
    revision = turn.get("revision") or 0

    if status == ReviewStatus.retry.value:
        target = retry_phase or DesignPhase.author.value
        if target not in (DesignPhase.plan.value, DesignPhase.author.value):
            raise DesignTurnError("retry_phase 须为 plan 或 author")
        current_revision = turn.get("revision") or 0
        if current_revision >= MAX_DESIGN_REVISION:
            _append_revision_limit_message(
                project_id,
                turn["id"],
                turn.get("job_id"),
                current_revision,
                blocked=True,
            )
            raise DesignTurnError(
                f"已达最大设计迭代次数（{MAX_DESIGN_REVISION}），"
                "请接受当前方案、手动编辑源码，或重新描述需求"
            )
        next_phase = target
        revision = current_revision + 1
        if revision >= MAX_DESIGN_REVISION:
            _append_revision_limit_message(
                project_id,
                turn["id"],
                turn.get("job_id"),
                revision,
                blocked=False,
            )
    elif status == ReviewStatus.pass_.value:
        next_phase = DesignPhase.done.value
    elif status == ReviewStatus.accept_warnings.value:
        next_phase = DesignPhase.done.value
    else:
        raise DesignTurnError(f"未知 review status: {status}")

    updated = _patch_turn(
        project_id,
        review=review,
        design_phase=next_phase,
        revision=revision,
    )
    maybe_finalize_turn(project_id)
    return updated or turn


def ensure_implicit_plan(
    project_id: str,
    turn_id: str,
    prompt: str | None,
) -> None:
    """When Agent skips report_design_plan, derive a minimal plan from the job prompt."""
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id or turn.get("plan"):
        return
    summary = (prompt or "").strip() or "Agent 建模任务"
    set_design_plan(
        project_id,
        turn_id,
        {
            "task_class": TaskClass.A.value,
            "summary": summary[:2000],
            "strategy": PlanStrategy.from_scratch.value,
            "assumptions": ["Agent 未提交 design plan，Engine 自动生成 implicit plan"],
            "modules": [],
        },
    )


def _try_auto_pass_review(project_id: str) -> None:
    """Close review when render succeeded but Agent did not call report_design_review."""
    turn = get_active_turn(project_id)
    if not turn:
        return
    if turn.get("review"):
        return
    if turn.get("agent_phase") != "replied":
        return
    if turn.get("render_phase") != "done":
        return
    if not turn.get("job_ids"):
        return
    if turn.get("design_phase") not in (
        DesignPhase.review.value,
        DesignPhase.render.value,
    ):
        return

    review = {
        "status": ReviewStatus.pass_.value,
        "notes": ["Engine 自动验收（Agent 未调用 report_design_review）"],
        "retry_phase": None,
        "recorded_at": _utcnow(),
    }
    _patch_turn(project_id, review=review, design_phase=DesignPhase.done.value)
    maybe_finalize_turn(project_id)


def _append_revision_limit_message(
    project_id: str,
    turn_id: str,
    job_id: str | None,
    revision: int,
    *,
    blocked: bool,
) -> None:
    marker = "设计迭代上限" if blocked else "最后一次自动迭代"
    for msg in reversed(storage.list_messages(project_id)):
        if msg.get("turn_id") != turn_id:
            continue
        if msg.get("role") != MessageRole.system.value:
            continue
        if marker in msg.get("content", ""):
            return

    if blocked:
        content = (
            f"设计迭代上限：已 retry {revision} 次，无法继续自动迭代。"
            "请接受当前方案、使用左栏「代码」手动修改，或重新描述需求。"
        )
    else:
        content = (
            f"最后一次自动迭代（第 {revision}/{MAX_DESIGN_REVISION} 次 retry）。"
            "若仍不满意，建议改述需求或手动编辑源码。"
        )
    storage.append_message(
        project_id,
        role=MessageRole.system,
        content=content,
        turn_id=turn_id,
        job_id=job_id,
    )


def set_agent_replied(project_id: str, turn_id: str, assistant_message_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    _patch_turn(
        project_id,
        assistant_message_id=assistant_message_id,
        agent_phase="replied",
    )
    _try_auto_pass_review(project_id)
    maybe_finalize_turn(project_id)


def set_agent_failed(project_id: str, turn_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return
    _patch_turn(project_id, agent_phase="failed", design_phase=DesignPhase.blocked.value)
    maybe_finalize_turn(project_id)


def sync_render_from_job(project_id: str, job: dict) -> None:
    turn_id = job.get("turn_id")
    if not turn_id:
        return
    turn = get_active_turn(project_id)
    if not turn or turn["id"] != turn_id:
        return

    status = job.get("status")
    fields: dict[str, Any] = {}
    if status == JobStatus.failed.value:
        fields["render_phase"] = "failed"
    elif status == JobStatus.succeeded.value:
        fields["render_phase"] = "done"
        if job.get("version") is not None:
            fields["version"] = job["version"]
        if turn.get("design_phase") == DesignPhase.render.value:
            fields["design_phase"] = DesignPhase.review.value
    elif status in (JobStatus.pending.value, JobStatus.running.value):
        fields["render_phase"] = "running"
        fields["job_id"] = job.get("id")
        fields["design_phase"] = DesignPhase.render.value
    else:
        return

    _patch_turn(project_id, **fields)
    if status == JobStatus.succeeded.value:
        _try_auto_pass_review(project_id)
    if status in (JobStatus.succeeded.value, JobStatus.failed.value):
        maybe_finalize_turn(project_id)


def maybe_finalize_turn(project_id: str) -> None:
    turn = get_active_turn(project_id)
    if not turn:
        return

    agent_phase = turn.get("agent_phase", "running")
    render_phase = turn.get("render_phase", "idle")
    design_phase = turn.get("design_phase", DesignPhase.intake.value)
    had_render = bool(turn.get("job_ids"))

    if agent_phase == "running":
        return
    if render_phase == "running":
        return

    if design_phase == DesignPhase.blocked.value:
        storage.update_project_meta(project_id, active_turn=None)
        return

    if not had_render and design_phase == DesignPhase.done.value and agent_phase == "replied":
        storage.update_project_meta(project_id, active_turn=None)
        return

    if had_render and render_phase == "done" and design_phase == DesignPhase.review.value:
        return

    if had_render and render_phase == "failed":
        storage.update_project_meta(project_id, active_turn=None)
        return

    if not had_render:
        storage.update_project_meta(project_id, active_turn=None)
        return

    if design_phase in TERMINAL_DESIGN_PHASES:
        storage.update_project_meta(project_id, active_turn=None)


def turn_out(project_id: str, active_job: dict | None = None) -> DesignTurnOut | None:
    if active_job:
        sync_render_from_job(project_id, active_job)
    turn = get_active_turn(project_id)
    if not turn:
        return None
    plan = turn.get("plan") or {}
    review = turn.get("review") or {}
    return DesignTurnOut(
        id=turn["id"],
        agent_phase=turn.get("agent_phase", "running"),
        render_phase=turn.get("render_phase", "idle"),
        design_phase=turn.get("design_phase", DesignPhase.intake.value),
        user_message_id=turn["user_message_id"],
        assistant_message_id=turn.get("assistant_message_id"),
        job_id=turn.get("job_id"),
        version=turn.get("version"),
        revision=turn.get("revision") or 0,
        plan_summary=plan.get("summary"),
        plan_strategy=plan.get("strategy"),
        plan_template_id=plan.get("template_id"),
        plan_assumptions=plan.get("assumptions") or [],
        plan_modules=plan.get("modules") or [],
        review_status=review.get("status"),
        review_notes=review.get("notes") or [],
    )
