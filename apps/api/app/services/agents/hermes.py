"""Hermes Agent — local gateway HTTP API (POST /v1/runs)."""

from __future__ import annotations

import asyncio
import shutil
import time

import httpx

from app.config import settings
from app.services.agents.base import (
    AgentAdapter,
    AgentAdapterError,
    AgentProviderInfo,
    AgentSessionHandle,
    TERMINAL_STATUSES,
)
from app.services.agents.prompt import build_agent_prompt

_TERMINAL = TERMINAL_STATUSES | {"COMPLETED", "FAILED", "CANCELLED", "STOPPED"}


def _cli_available() -> bool:
    return shutil.which(settings.hermes_bin) is not None


def _auth_headers() -> dict[str, str]:
    key = settings.hermes_api_key.strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


async def _gateway_ready() -> bool:
    if not _cli_available():
        return False
    url = f"{settings.hermes_api_base.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
        return resp.status_code == 200
    except Exception:
        return False


class HermesAdapter(AgentAdapter):
    """Hermes Agent via local `hermes gateway` API server."""

    id = "hermes"
    title = "Hermes Agent"
    kind = "local"

    def info(self) -> AgentProviderInfo:
        configured = _cli_available()
        note = ""
        if not configured:
            note = f"未找到 `{settings.hermes_bin}` CLI；请安装 Hermes Agent 并配置 notion3d MCP"
        else:
            note = "需运行 make dev AGENT=hermes（或手动 hermes gateway）"
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
        base.ready = await _gateway_ready()
        if base.configured and not base.ready:
            base.note = "需运行 make dev AGENT=hermes 或 `hermes gateway`（API :8642）"
        return base

    def session_key(self, project_id: str) -> str:
        return f"notion3d-{project_id}"

    def _base_url(self) -> str:
        return settings.hermes_api_base.rstrip("/")

    async def start_turn(
        self,
        project_id: str,
        user_content: str,
        *,
        session_id: str | None = None,
        region: str | None = None,
        turn_id: str | None = None,
        latest_version: int | None = None,
    ) -> AgentSessionHandle:
        logical_id = session_id or self.session_key(project_id)
        prompt = build_agent_prompt(
            project_id,
            user_content,
            turn_id=turn_id,
            region=region,
            latest_version=latest_version,
        )
        url = f"{self._base_url()}/v1/runs"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json={"input": prompt, "session_id": logical_id},
                headers=_auth_headers(),
            )
        if resp.status_code >= 400:
            raise AgentAdapterError(f"Hermes API {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        run_id = data.get("run_id") or data.get("id")
        if not run_id:
            raise AgentAdapterError(f"Hermes 未返回 run_id: {data}")
        return AgentSessionHandle(
            provider=self.id,
            session_id=data.get("session_id") or logical_id,
            run_id=str(run_id),
            external_url=None,
        )

    async def run_status(self, handle: AgentSessionHandle) -> str:
        url = f"{self._base_url()}/v1/runs/{handle.run_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=_auth_headers())
        if resp.status_code >= 400:
            return "UNKNOWN"
        return str(resp.json().get("status", "UNKNOWN")).upper()

    async def collect_reply(self, handle: AgentSessionHandle) -> str:
        url = f"{self._base_url()}/v1/runs/{handle.run_id}"
        deadline = time.monotonic() + 600.0
        last_status = "RUNNING"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            while time.monotonic() < deadline:
                resp = await client.get(url, headers=_auth_headers())
                if resp.status_code >= 400:
                    raise AgentAdapterError(f"Hermes API {resp.status_code}: {resp.text[:500]}")
                data = resp.json()
                status = str(data.get("status", "")).upper()
                last_status = status or last_status

                if status in _TERMINAL:
                    if status in {"FAILED", "ERROR", "CANCELLED"}:
                        err = data.get("error") or data.get("message") or status
                        raise AgentAdapterError(str(err))
                    output = (data.get("output") or "").strip()
                    if output:
                        return output
                    if status in {"COMPLETED", "FINISHED", "SUCCEEDED", "DONE"}:
                        raise AgentAdapterError("Agent 未返回文本回复，请重试或查看预览是否已更新。")
                    raise AgentAdapterError(f"Hermes 无回复（status={status}）")

                await asyncio.sleep(1.5)

        raise AgentAdapterError(f"Hermes 超时（status={last_status}）")
