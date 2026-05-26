"""Web Turn bridge sidecar — HTTP adapter to local agent runtime + notion3d MCP."""

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
from app.services.web_turn_config import WEB_TURN_BRIDGE


def _configured() -> bool:
    return bool(settings.web_turn_bridge_api_key.strip())


async def _bridge_ready() -> bool:
    if not _configured():
        return False
    url = f"{settings.web_turn_bridge_base.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return False
        data = resp.json()
        return bool(
            data.get("api_ready")
            or data.get("api_key_configured")
            or data.get("cursor_api_ready")
        )
    except Exception:
        return False


class BridgeAdapter(AgentAdapter):
    """Web Turn `bridge` — agent-bridge :8787 → notion3d-mcp → Engine."""

    id = WEB_TURN_BRIDGE
    title = "Web Turn bridge"
    kind = "http_sidecar"

    def info(self) -> AgentProviderInfo:
        configured = _configured()
        note = ""
        if not configured:
            note = "部署层：配置 CURSOR_API_KEY"
        elif not settings.web_turn_bridge_base.strip():
            note = "部署层：配置 NOTION3D_WEB_TURN_BRIDGE_BASE"
        else:
            note = "部署层：make dev WEB_TURN=bridge 或 make bridge"
        return AgentProviderInfo(
            id=self.id,
            title=self.title,
            kind=self.kind,
            configured=configured,
            ready=False,
            note=note,
        )

    async def info_ready(self) -> AgentProviderInfo:
        base = self.info()
        base.ready = await _bridge_ready()
        if base.configured and not base.ready and "make bridge" not in base.note:
            base.note = "部署层：make dev WEB_TURN=bridge 或 make bridge"
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
        turn_id: str | None = None,
        latest_version: int | None = None,
        images: list[dict[str, str]] | None = None,
    ) -> AgentSessionHandle:
        logical_id = session_id or self.session_key(project_id)
        prompt = build_agent_prompt(
            project_id,
            user_content,
            turn_id=turn_id,
            region=region,
            latest_version=latest_version,
        )
        payload: dict = {"agentId": logical_id, "prompt": prompt}
        if images:
            payload["images"] = [
                {
                    "data": img.get("data") or "",
                    "mimeType": img.get("mime_type") or img.get("mimeType") or "image/png",
                }
                for img in images
            ]
        url = f"{settings.web_turn_bridge_base.rstrip('/')}/v1/turn"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json=payload,
            )
        if resp.status_code >= 400:
            raise AgentAdapterError(f"Web Turn bridge {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        return AgentSessionHandle(
            provider=self.id,
            session_id=data.get("agentId") or logical_id,
            run_id=data["runId"],
            external_url=None,
        )

    async def run_status(self, handle: AgentSessionHandle) -> str:
        url = f"{settings.web_turn_bridge_base.rstrip('/')}/v1/runs/{handle.run_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        if resp.status_code >= 400:
            return "UNKNOWN"
        return str(resp.json().get("status", "UNKNOWN"))

    async def collect_reply(self, handle: AgentSessionHandle) -> str:
        url = f"{settings.web_turn_bridge_base.rstrip('/')}/v1/runs/{handle.run_id}/wait"
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            resp = await client.get(url)
        if resp.status_code >= 400:
            raise AgentAdapterError(f"Web Turn bridge {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        if data.get("error"):
            raise AgentAdapterError(str(data["error"]))
        reply = (data.get("result") or "").strip()
        if reply:
            return reply
        status = str(data.get("status", ""))
        if status == "FINISHED":
            raise AgentAdapterError("Agent 未返回文本回复，请重试或查看预览是否已更新。")
        raise AgentAdapterError(f"Agent 无回复（status={status}）")
