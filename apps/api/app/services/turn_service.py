"""Unified design turn — agent only (no template fallback)."""

from __future__ import annotations

import logging

from datetime import datetime, timezone

from app.models.schemas import AgentRunOut, AgentTurnIn, MessageRole, TurnOut
from app.services import job_store, storage
from app.services.agents import (
    AgentAdapterError,
    AgentSessionHandle,
    get_adapter,
    resolve_adapter,
)

logger = logging.getLogger(__name__)

BLOCKED_NO_AGENT = (
    "Web 对话需要连接设计助手。"
    "点击右上角「助手」查看配置（推荐 CURSOR_API_KEY + make dev）。"
)


def format_user_text(body: AgentTurnIn) -> str:
    user_text = body.content
    if body.region:
        user_text = f"{body.content}\n\n📍 部位：{body.region}"
    elif body.pick:
        label = body.pick.label or f"({body.pick.x:.1f}, {body.pick.y:.1f}, {body.pick.z:.1f})"
        user_text = f"{body.content}\n\n📍 3D 点选：{label}"
    return user_text


async def finish_agent_run(project_id: str, pending: dict) -> None:
    provider_id = pending["provider"]
    adapter = get_adapter(provider_id)
    if not adapter:
        storage.append_message(project_id, MessageRole.assistant, "设计助手连接异常，请重试。")
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
        storage.append_message(project_id, MessageRole.assistant, reply)
    except Exception as exc:
        logger.exception("agent run failed project=%s provider=%s", project_id, provider_id)
        storage.append_message(
            project_id,
            MessageRole.assistant,
            f"设计助手处理失败：{exc}",
        )
    finally:
        storage.update_project_meta(project_id, agent_run_pending=None)


async def handle_turn(
    project_id: str,
    body: AgentTurnIn,
    *,
    start_agent_turn,
) -> TurnOut:
    """Route turn to agent. Callers inject background task starter to avoid circular imports."""
    user_text = format_user_text(body)
    storage.append_message(project_id, MessageRole.user, user_text)

    meta = storage.load_meta(project_id)
    adapter = resolve_adapter(meta.get("agent_provider"))

    if not adapter:
        msg = storage.append_message(project_id, MessageRole.assistant, BLOCKED_NO_AGENT)
        return TurnOut(routing="blocked", assistant_message_id=msg["id"], reason="no_agent")

    try:
        handle = await adapter.start_turn(
            project_id,
            user_text,
            session_id=meta.get("agent_session_id"),
            region=body.region,
        )
        pending = {
            "provider": handle.provider,
            "session_id": handle.session_id,
            "run_id": handle.run_id,
            "external_url": handle.external_url,
            "extra": handle.extra,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        storage.update_project_meta(
            project_id,
            agent_session_id=handle.session_id,
            agent_run_pending=pending,
        )
        msg = storage.append_message(
            project_id,
            MessageRole.assistant,
            "设计助手正在理解需求并建模，左侧将陆续出现预览…",
        )
        start_agent_turn(project_id, pending)
        return TurnOut(
            routing="agent",
            assistant_message_id=msg["id"],
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
            MessageRole.assistant,
            f"设计助手暂时不可用：{exc}",
        )
        return TurnOut(routing="blocked", assistant_message_id=msg["id"], reason="agent_error")


def active_job_for_project(project_id: str) -> dict | None:
    jobs = job_store.list_active_jobs(project_id)
    return jobs[0] if jobs else None
