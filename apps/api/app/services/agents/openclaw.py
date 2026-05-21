"""OpenClaw local agent — `openclaw agent --local` on the same machine as Notion3D."""

from __future__ import annotations

import asyncio
import json
import shutil
import uuid

from app.config import settings
from app.services.agents.base import (
    AgentAdapter,
    AgentAdapterError,
    AgentProviderInfo,
    AgentSessionHandle,
)
from app.services.agents.prompt import build_agent_prompt


def _cli_available() -> bool:
    return shutil.which(settings.openclaw_bin) is not None


class OpenClawAdapter(AgentAdapter):
    id = "openclaw"
    title = "OpenClaw"
    kind = "local"

    def info(self) -> AgentProviderInfo:
        configured = _cli_available()
        note = ""
        if not configured:
            note = f"未找到 `{settings.openclaw_bin}` CLI；请安装 OpenClaw 并配置 notion3d MCP"
        return AgentProviderInfo(
            id=self.id,
            title=self.title,
            kind=self.kind,
            configured=configured,
            ready=configured,
            note=note,
        )

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
        sid = session_id or self.session_key(project_id)
        prompt = build_agent_prompt(project_id, user_content, region=region)
        run_id = str(uuid.uuid4())
        return AgentSessionHandle(
            provider=self.id,
            session_id=sid,
            run_id=run_id,
            extra={"prompt": prompt},
        )

    async def run_status(self, handle: AgentSessionHandle) -> str:
        # CLI 模式：collect_reply 阻塞至完成；pending 期间视为 RUNNING
        return "RUNNING"

    async def collect_reply(self, handle: AgentSessionHandle) -> str:
        prompt = handle.extra.get("prompt")
        if not prompt:
            raise AgentAdapterError("OpenClaw 缺少 prompt")

        proc = await asyncio.create_subprocess_exec(
            settings.openclaw_bin,
            "agent",
            "--session-id",
            handle.session_id,
            "--message",
            prompt,
            "--local",
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode().strip() or stdout.decode().strip() or "openclaw agent 失败"
            raise AgentAdapterError(err)

        try:
            data = json.loads(stdout.decode())
        except json.JSONDecodeError as exc:
            raise AgentAdapterError(f"OpenClaw 返回非 JSON: {stdout.decode()[:300]}") from exc

        texts: list[str] = []
        for item in data.get("payloads") or []:
            text = item.get("text")
            if text:
                texts.append(text.strip())
        if texts:
            return "\n\n".join(texts)
        return "OpenClaw Agent 已完成。若已提交建模，请查看左侧 3D 预览。"
