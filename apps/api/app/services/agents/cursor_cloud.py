"""Cursor Cloud Agents API — NOT Cursor IDE. See https://cursor.com/docs/cloud-agent/api/endpoints"""

from __future__ import annotations

import asyncio
import json
from typing import Any

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


def _ready() -> bool:
    if not _configured():
        return False
    base = (settings.public_api_base or "").strip().lower()
    if not base:
        return False
    return "localhost" not in base and "127.0.0.1" not in base


def _auth() -> tuple[str, str]:
    return settings.cursor_api_key.strip(), ""


def _mcp_api_base() -> str:
    return (settings.public_api_base or "").strip().rstrip("/")


def _mcp_servers() -> list[dict[str, Any]]:
    """Cloud VM has no local notion3d-mcp; bootstrap via pip from GitHub."""
    mcp_env = {
        "NOTION3D_API_BASE": _mcp_api_base(),
        "NOTION3D_WEB_BASE": settings.web_base_url.rstrip("/"),
    }
    if settings.notion3d_mcp_command.strip() == "notion3d-mcp":
        return [
            {
                "name": "notion3d",
                "type": "stdio",
                "command": "bash",
                "args": [
                    "-c",
                    "pip install -q "
                    "'notion3d-mcp @ git+https://github.com/manwjh/Notion3D.git#subdirectory=apps/mcp-server' "
                    "&& exec notion3d-mcp",
                ],
                "env": mcp_env,
            }
        ]
    return [
        {
            "name": "notion3d",
            "type": "stdio",
            "command": settings.notion3d_mcp_command,
            "env": mcp_env,
        }
    ]


class CursorCloudAdapter(AgentAdapter):
    """Programmatic Cloud Agent via POST https://api.cursor.com/v1/agents."""

    id = "cursor_cloud"
    title = "Cursor Cloud Agents API"
    kind = "cloud"

    def __init__(self) -> None:
        self._base = settings.cursor_api_base.rstrip("/")

    def info(self) -> AgentProviderInfo:
        note = ""
        if _configured() and not _ready():
            note = "Cloud Agent 在 Cursor 云端运行，需 NOTION3D_PUBLIC_API_BASE（与 Cursor IDE 无关）"
        elif not _configured():
            note = "在 .env 配置 CURSOR_API_KEY（Dashboard → Integrations）"
        return AgentProviderInfo(
            id=self.id,
            title=self.title,
            kind=self.kind,
            configured=_configured(),
            ready=_ready(),
            note=note,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        url = f"{self._base}{path}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(
                method,
                url,
                auth=_auth(),
                json=json_body,
                headers={"Content-Type": "application/json"},
            )
        if resp.status_code >= 400:
            raise AgentAdapterError(f"Cursor API {resp.status_code}: {resp.text[:500]}")
        return resp.json() if resp.content else {}

    async def start_turn(
        self,
        project_id: str,
        user_content: str,
        *,
        session_id: str | None = None,
        region: str | None = None,
    ) -> AgentSessionHandle:
        prompt = build_agent_prompt(project_id, user_content, region=region)
        if session_id:
            run_id = await self._create_run(session_id, prompt)
            agent_id = session_id
        else:
            agent_id, run_id = await self._create_agent(prompt)
        return AgentSessionHandle(
            provider=self.id,
            session_id=agent_id,
            run_id=run_id,
            external_url=f"https://cursor.com/agents?id={agent_id}",
        )

    async def _create_agent(self, prompt_text: str) -> tuple[str, str]:
        data = await self._request(
            "POST",
            "/v1/agents",
            json_body={
                "prompt": {"text": prompt_text},
                "model": {"id": settings.cursor_model},
                "mcpServers": _mcp_servers(),
            },
            timeout=120.0,
        )
        return data["agent"]["id"], data["run"]["id"]

    async def _create_run(self, agent_id: str, prompt_text: str) -> str:
        body = {"prompt": {"text": prompt_text}, "mcpServers": _mcp_servers()}
        try:
            data = await self._request(
                "POST",
                f"/v1/agents/{agent_id}/runs",
                json_body=body,
                timeout=120.0,
            )
        except AgentAdapterError as exc:
            if "409" not in str(exc):
                raise
            await asyncio.sleep(2)
            data = await self._request(
                "POST",
                f"/v1/agents/{agent_id}/runs",
                json_body=body,
                timeout=120.0,
            )
        return data["run"]["id"]

    async def run_status(self, handle: AgentSessionHandle) -> str:
        run = await self._request(
            "GET",
            f"/v1/agents/{handle.session_id}/runs/{handle.run_id}",
            timeout=30.0,
        )
        return str(run.get("status", "UNKNOWN"))

    async def collect_reply(self, handle: AgentSessionHandle) -> str:
        url = f"{self._base}/v1/agents/{handle.session_id}/runs/{handle.run_id}/stream"
        parts: list[str] = []
        error: str | None = None

        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
            async with client.stream(
                "GET",
                url,
                auth=_auth(),
                headers={"Accept": "text/event-stream"},
            ) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    raise AgentAdapterError(
                        f"Cursor stream {resp.status_code}: {body.decode()[:500]}"
                    )
                event = "message"
                async for raw in resp.aiter_lines():
                    line = raw.strip()
                    if not line:
                        continue
                    if line.startswith("event:"):
                        event = line.split(":", 1)[1].strip()
                        continue
                    if not line.startswith("data:"):
                        continue
                    payload = json.loads(line.split(":", 1)[1].strip())
                    if event == "assistant" and payload.get("text"):
                        parts.append(payload["text"])
                    elif event == "error":
                        error = payload.get("message") or str(payload)

        if error:
            raise AgentAdapterError(error)
        reply = "".join(parts).strip()
        if reply:
            return reply
        status = await self.run_status(handle)
        if status == "FINISHED":
            return "Cloud Agent 已完成。若已提交建模，请查看左侧 3D 预览。"
        raise AgentAdapterError(f"Cloud Agent 无回复（status={status}）")
