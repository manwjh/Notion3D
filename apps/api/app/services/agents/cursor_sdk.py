"""Cursor TypeScript SDK — local runtime. Not Cursor IDE."""

from __future__ import annotations

import httpx

from app.config import settings
from app.services.agents.base import (
    AgentAdapter,
    AgentAdapterError,
    AgentProviderInfo,
    AgentSessionHandle,
)
from app.services.agents.prompt import build_agent_prompt


def _configured() -> bool:
    return bool(settings.cursor_api_key.strip())


async def _bridge_ready() -> bool:
    if not _configured():
        return False
    url = f"{settings.cursor_sdk_bridge_base.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return bool(data.get("cursor_api_ready"))
    except Exception:
        return False


class CursorSdkAdapter(AgentAdapter):
    """Local @cursor/sdk agent — MCP on 127.0.0.1, no public tunnel."""

    id = "cursor_sdk"
    title = "Cursor SDK (local)"
    kind = "local"

    def info(self) -> AgentProviderInfo:
        note = ""
        configured = _configured()
        if not configured:
            note = "在 .env 配置 CURSOR_API_KEY（与 Cursor IDE 无关）"
        elif not settings.cursor_sdk_bridge_base.strip():
            note = "需配置 NOTION3D_CURSOR_SDK_BRIDGE_BASE"
        else:
            note = "需运行 agent-bridge：make bridge 或 make dev"
        return AgentProviderInfo(
            id=self.id,
            title=self.title,
            kind=self.kind,
            configured=configured,
            ready=False,  # resolved async in registry via refresh if needed
            note=note,
        )

    async def info_ready(self) -> AgentProviderInfo:
        base = self.info()
        base.ready = await _bridge_ready()
        if base.configured and not base.ready and "make bridge" not in base.note:
            base.note = "需运行 agent-bridge：make bridge 或 make dev"
        return base

    def session_key(self, project_id: str) -> str:
        return f"notion3d-{project_id}"

    async def start_turn(
        self,
        project_id: str,
        user_content: str,
        *,
        session_id: str | None = None,
        region: str | None = None,
    ) -> AgentSessionHandle:
        logical_id = session_id or self.session_key(project_id)
        prompt = build_agent_prompt(project_id, user_content, region=region)
        url = f"{settings.cursor_sdk_bridge_base.rstrip('/')}/v1/turn"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json={"agentId": logical_id, "prompt": prompt},
            )
        if resp.status_code >= 400:
            raise AgentAdapterError(f"SDK bridge {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        return AgentSessionHandle(
            provider=self.id,
            session_id=data.get("agentId") or logical_id,
            run_id=data["runId"],
            external_url=None,
        )

    async def run_status(self, handle: AgentSessionHandle) -> str:
        url = f"{settings.cursor_sdk_bridge_base.rstrip('/')}/v1/runs/{handle.run_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        if resp.status_code >= 400:
            return "UNKNOWN"
        return str(resp.json().get("status", "UNKNOWN"))

    async def collect_reply(self, handle: AgentSessionHandle) -> str:
        url = f"{settings.cursor_sdk_bridge_base.rstrip('/')}/v1/runs/{handle.run_id}/wait"
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            resp = await client.get(url)
        if resp.status_code >= 400:
            raise AgentAdapterError(f"SDK bridge {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        if data.get("error"):
            raise AgentAdapterError(str(data["error"]))
        reply = (data.get("result") or "").strip()
        if reply:
            return reply
        status = str(data.get("status", ""))
        if status == "FINISHED":
            return "Cursor SDK Agent 已完成。若已提交建模，请查看左侧 3D 预览。"
        raise AgentAdapterError(f"SDK Agent 无回复（status={status}）")
