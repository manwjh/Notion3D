"""Poll Web Turn bridge for live Agent tool activity."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.config import settings
from app.services import project_events, storage
from app.services.web_turn_config import WEB_TURN_BRIDGE

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 1.2


async def fetch_bridge_run(run_id: str) -> dict:
    base = settings.web_turn_bridge_base.rstrip("/")
    url = f"{base}/v1/runs/{run_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("bridge run poll failed run=%s: %s", run_id, exc)
        return {}


async def fetch_bridge_activity(run_id: str) -> list[dict]:
    base = settings.web_turn_bridge_base.rstrip("/")
    url = f"{base}/v1/runs/{run_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        activity = data.get("activity")
        return list(activity) if isinstance(activity, list) else []
    except Exception as exc:
        logger.debug("bridge activity poll failed run=%s: %s", run_id, exc)
        return []


def _activity_changed(prev: list[dict], current: list[dict]) -> bool:
    if len(prev) != len(current):
        return True
    for a, b in zip(prev, current):
        if a.get("id") != b.get("id"):
            return True
        if a.get("status") != b.get("status"):
            return True
        if a.get("label") != b.get("label"):
            return True
    return False


async def sync_agent_activity_loop(project_id: str) -> None:
    """While agent_run_pending, mirror bridge tool steps into project meta + SSE."""
    while True:
        meta = storage.load_meta(project_id)
        pending = meta.get("agent_run_pending")
        if not pending:
            return

        provider = pending.get("provider")
        run_id = pending.get("run_id")
        if provider == WEB_TURN_BRIDGE and run_id:
            run = await fetch_bridge_run(run_id)
            activity = list(run.get("activity") or [])
            prev = list(meta.get("agent_activity") or [])
            if _activity_changed(prev, activity):
                storage.update_project_meta(project_id, agent_activity=activity)
                project_events.notify(project_id)
            status = str(run.get("status") or "").upper()
            if status in ("FINISHED", "ERROR"):
                await heal_stale_agent_pending(project_id, pending, run)
                return
        else:
            await asyncio.sleep(POLL_INTERVAL_SEC)
            continue

        await asyncio.sleep(POLL_INTERVAL_SEC)


def clear_agent_activity(project_id: str) -> None:
    storage.update_project_meta(project_id, agent_activity=[])


async def heal_stale_agent_pending(
    project_id: str,
    pending: dict,
    run: dict | None = None,
) -> None:
    """Bridge run finished but Engine still shows agent.active — complete the turn."""
    from app.services import turn_service

    turn_id = pending.get("turn_id")
    if turn_id:
        for msg in reversed(storage.list_messages(project_id)):
            if msg.get("turn_id") != turn_id:
                continue
            if msg.get("role") == "assistant":
                storage.update_project_meta(project_id, agent_run_pending=None)
                project_events.notify(project_id)
                return

    run = run or await fetch_bridge_run(pending.get("run_id") or "")
    status = str(run.get("status") or "").upper()
    if status not in ("FINISHED", "ERROR"):
        return

    # Avoid duplicate finish if background task is still clearing pending.
    meta = storage.load_meta(project_id)
    if not meta.get("agent_run_pending"):
        return

    await turn_service.finish_agent_run(project_id, pending)

