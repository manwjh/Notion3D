"""Web Turn gateway sidecar — HTTP Runs API → agent runtime + notion3d MCP."""

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
from app.services.web_turn_config import WEB_TURN_GATEWAY

_TERMINAL = TERMINAL_STATUSES | {"COMPLETED", "FAILED", "CANCELLED", "STOPPED"}


def _cli_available() -> bool:
    return shutil.which(settings.web_turn_gateway_bin) is not None


def _auth_headers() -> dict[str, str]:
    key = settings.web_turn_gateway_api_key.strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


async def _gateway_ready() -> bool:
    if not _cli_available():
        return False
    url = f"{settings.web_turn_gateway_base.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
        return resp.status_code == 200
    except Exception:
        return False


class GatewayAdapter(AgentAdapter):
    """Web Turn `gateway` — HTTP Runs API :8642 → notion3d-mcp → Engine."""

    id = WEB_TURN_GATEWAY
    title = "Web Turn gateway"
    kind = "http_sidecar"

    def info(self) -> AgentProviderInfo:
        configured = _cli_available()
        note = ""
        if not configured:
            note = f"部署层：未找到 `{settings.web_turn_gateway_bin}` 可执行文件"
        else:
            note = "部署层：make dev WEB_TURN=gateway"
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
            base.note = "部署层：make dev WEB_TURN=gateway 或手动启动 gateway（:8642）"
        return base

    def session_key(self, project_id: str) -> str:
        return f"notion3d-{project_id}"

    def _base_url(self) -> str:
        return settings.web_turn_gateway_base.rstrip("/")

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
        if images:
            prompt = (
                f"{prompt}\n\n用户附带了 {len(images)} 张截图。"
                "若 gateway 不支持视觉，请结合 wait_job 的 spatial_summary 与 validation_warnings 验收。"
            )
        url = f"{self._base_url()}/v1/runs"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json={"input": prompt, "session_id": logical_id},
                headers=_auth_headers(),
            )
        if resp.status_code >= 400:
            raise AgentAdapterError(f"Web Turn gateway {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        run_id = data.get("run_id") or data.get("id")
        if not run_id:
            raise AgentAdapterError(f"Web Turn gateway 未返回 run_id: {data}")
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
                    raise AgentAdapterError(f"Web Turn gateway {resp.status_code}: {resp.text[:500]}")
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
                    raise AgentAdapterError(f"Agent 无回复（status={status}）")

                await asyncio.sleep(1.5)

        raise AgentAdapterError(f"Web Turn gateway 超时（status={last_status}）")
