"""Unified design turn — agent only (no template fallback)."""

from __future__ import annotations

import logging
import uuid

from datetime import datetime, timezone

from app.models.schemas import AgentRunOut, AgentTurnIn, MessageRole, TurnOut
from app.services import design_turn, job_store, storage
from app.services.agents import (
    AgentAdapterError,
    AgentSessionHandle,
    get_adapter,
    refresh_provider_cache,
    resolve_adapter_live,
)
from app.services.web_turn_config import normalize_web_turn

logger = logging.getLogger(__name__)

BLOCKED_NO_AGENT = "自然语言建模暂不可用，请使用左栏编辑模型。"


def format_user_text(body: AgentTurnIn) -> str:
    user_text = body.content
    if body.pick:
        if body.pick.element:
            label = body.pick.label or body.pick.element
            user_text = f"{body.content}\n\n🎯 选中部件：{label} ({body.pick.element})"
        else:
            label = body.pick.label or f"({body.pick.x:.1f}, {body.pick.y:.1f}, {body.pick.z:.1f})"
            user_text = f"{body.content}\n\n📍 3D 点选：{label}"
    if body.images:
        user_text = (
            f"{user_text}\n\n🖼 用户附带了 {len(body.images)} 张截图"
            "（已传入视觉通道；请对照预览、spatial_digest 与 validation_warnings 决定是否继续改 forge）。"
        )
    return user_text


async def finish_agent_run(project_id: str, pending: dict) -> None:
    turn_id = pending.get("turn_id")
    meta = storage.load_meta(project_id)
    live = meta.get("agent_run_pending")
    if not live or live.get("run_id") != pending.get("run_id"):
        return
    if turn_id:
        for msg in reversed(storage.list_messages(project_id)):
            if msg.get("turn_id") != turn_id:
                continue
            if msg.get("role") in ("assistant", "system"):
                storage.update_project_meta(project_id, agent_run_pending=None)
                return

    provider_id = pending["provider"]
    adapter = get_adapter(provider_id)
    if not adapter:
        storage.append_message(
            project_id,
            MessageRole.system,
            "建模服务异常，请重试。",
            turn_id=turn_id,
        )
        if turn_id:
            design_turn.set_agent_failed(project_id, turn_id)
        storage.update_project_meta(project_id, agent_run_pending=None)
        return

    handle = AgentSessionHandle(
        provider=provider_id,
        session_id=pending["session_id"],
        run_id=pending["run_id"],
        external_url=pending.get("external_url"),
        extra=pending.get("extra") or {},
    )
    try:
        reply = await adapter.collect_reply(handle)
        reply = reply.strip()
        if not reply:
            raise ValueError("empty reply")
        msg = storage.append_message(
            project_id,
            MessageRole.assistant,
            reply,
            turn_id=turn_id,
        )
        if turn_id:
            design_turn.set_agent_replied(project_id, turn_id, msg["id"])
    except Exception as exc:
        logger.exception("agent run failed project=%s provider=%s", project_id, provider_id)
        storage.append_message(
            project_id,
            MessageRole.system,
            f"建模失败：{exc}",
            turn_id=turn_id,
        )
        if turn_id:
            design_turn.set_agent_failed(project_id, turn_id)
    finally:
        from app.services import agent_activity, project_events
        from app.services.web_turn_config import WEB_TURN_BRIDGE

        if provider_id == WEB_TURN_BRIDGE and pending.get("run_id"):
            activity = await agent_activity.fetch_bridge_activity(pending["run_id"])
            if activity:
                storage.update_project_meta(project_id, agent_activity=activity)
                project_events.notify(project_id)
        storage.update_project_meta(project_id, agent_run_pending=None)


async def handle_turn(
    project_id: str,
    body: AgentTurnIn,
    *,
    start_agent_turn,
) -> TurnOut:
    """Route turn to agent. Callers inject background task starter to avoid circular imports."""
    user_text = format_user_text(body)
    turn_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    saved_images: list[dict] = []
    if body.images:
        from app.services import message_attachments

        saved_images = message_attachments.save_turn_images(
            project_id,
            message_id,
            [img.model_dump() for img in body.images],
        )
    user_msg = storage.append_message(
        project_id,
        MessageRole.user,
        user_text,
        turn_id=turn_id,
        message_id=message_id,
        images=saved_images or None,
    )
    from app.services import agent_activity

    agent_activity.clear_agent_activity(project_id)
    design_turn.begin_turn(project_id, user_msg["id"], turn_id=turn_id)

    await refresh_provider_cache()

    meta = storage.load_meta(project_id)
    meta_turn = meta.get("web_turn") or meta.get("agent_provider")
    adapter = await resolve_adapter_live(normalize_web_turn(meta_turn) if meta_turn else None)
    latest_version = meta.get("latest_version")

    if not adapter:
        msg = storage.append_message(
            project_id,
            MessageRole.system,
            BLOCKED_NO_AGENT,
            turn_id=turn_id,
        )
        design_turn.set_agent_failed(project_id, turn_id)
        return TurnOut(
            turn_id=turn_id,
            routing="blocked",
            assistant_message_id=msg["id"],
            reason="no_agent",
        )

    try:
        region = body.region
        if not region and body.pick and body.pick.element:
            label = body.pick.label or body.pick.element
            region = f"{label} ({body.pick.element})"
        elif not region and body.pick:
            region = body.pick.label
        handle = await adapter.start_turn(
            project_id,
            user_text,
            session_id=meta.get("agent_session_id"),
            region=region,
            turn_id=turn_id,
            latest_version=latest_version,
            images=[img.model_dump() for img in body.images] if body.images else None,
        )
        pending = {
            "provider": handle.provider,
            "session_id": handle.session_id,
            "run_id": handle.run_id,
            "external_url": handle.external_url,
            "extra": handle.extra,
            "turn_id": turn_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        storage.update_project_meta(
            project_id,
            agent_session_id=handle.session_id,
            agent_run_pending=pending,
        )
        start_agent_turn(project_id, pending)
        return TurnOut(
            turn_id=turn_id,
            routing="agent",
            assistant_message_id=None,
            agent=AgentRunOut(
                provider=handle.provider,
                session_id=handle.session_id,
                run_id=handle.run_id,
                status="RUNNING",
                external_url=handle.external_url,
            ),
        )
    except AgentAdapterError as exc:
        msg = storage.append_message(
            project_id,
            MessageRole.system,
            f"自然语言建模暂不可用：{exc}",
            turn_id=turn_id,
        )
        design_turn.set_agent_failed(project_id, turn_id)
        return TurnOut(
            turn_id=turn_id,
            routing="blocked",
            assistant_message_id=msg["id"],
            reason="agent_error",
        )


def active_job_for_project(project_id: str) -> dict | None:
    jobs = job_store.list_active_jobs(project_id)
    return jobs[0] if jobs else None
